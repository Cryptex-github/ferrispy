from __future__ import annotations
from types import coroutine

import aiohttp
from typing import TYPE_CHECKING, Union, Coroutine

from .handler import EventHandler
from .utils import from_json, to_json
from .errors import WebsocketException, Reconnect

if TYPE_CHECKING:
    from .http import HTTPClient
    from .types import Data
    from .types.ws import WsConnectionInfo
    from .client import Client


class Websocket:
    """The class that interfaces with FerrisChat's websockets."""

    def __init__(self, client: Client) -> None:
        self.ws: aiohttp.ClientWebSocketResponse

        self._handler: EventHandler = EventHandler(client._connection)

        self._http: HTTPClient = client._connection._http
        self.dispatch: Coroutine = client.dispatch
        self._ws_url: str = ''

    async def prepare(self) -> None:
        """Retrieves the URL needed for websocket connection."""
        response: WsConnectionInfo = await self._http.api.ws.info.get()  # type: ignore
        self._ws_url = response['url']

    async def handle(self, data: dict) -> None:
        """Handles a message received from the websocket."""
        self._handler.handle(data)

    async def _parse_and_handle(self, data: Union[str, bytes]) -> None:
        if isinstance(data, (str, bytes)):
            _data: dict = from_json(data)
            await self.handle(_data)

    async def send(self, data: dict, /):
        _data = to_json(data)
        await self.ws.send_str(_data)

    async def connect(self) -> None:
        """Establishes a websocket connection with FerrisChat."""
        if not self._ws_url:
            await self.prepare()

        self.ws = await self._http.session.ws_connect(self._ws_url, heartbeat=45)

        await self.send(
            {'c': 'Identify', 'd': {'token': self._http.token, 'intents': 0}}
        )

        await self.dispatch('connect')
        async for message in self.ws:
            if message.type in {aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY}:
                await self._parse_and_handle(message.data)
            elif message.type is aiohttp.WSMsgType.ERROR:
                raise WebsocketException(message.data)
            elif message.type in (
                aiohttp.WSMsgType.CLOSED,
                aiohttp.WSMsgType.CLOSING,
                aiohttp.WSMsgType.CLOSE,
            ):
                raise Reconnect  # TODO: Reconnect here

    async def close(self) -> None:
        """Closes the current websocket connection."""
        await self.ws.close()
