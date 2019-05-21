# -*- coding: utf-8 -*-

import ujson
import asyncio

from aioli.package.service import BaseService
from aioli.exceptions import NoMatchFound, AioliException
from .utils import serialize_columns


class LivestatusService(BaseService):
    loop = None
    _host = None
    _port = None

    async def init(self, host, port):
        self._host = host
        self._port = port

    async def _get_connection(self):
        return await asyncio.open_connection(host=self._host, port=self._port, loop=self.loop)

    def _format_response(self, header, body):
        return [dict(zip(header, row)) for row in body]

    async def _write(self, writer, command):
        command.append("OutputFormat: json\n")
        cmd_str = '\n'.join(command).encode('utf-8')

        writer.write(cmd_str)

        if writer.can_write_eof():
            writer.write_eof()

        await writer.drain()

    async def _read(self, reader):
        chunks = bytes()

        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break

            chunks += chunk

        return chunks

    async def send(self, command, fields=None):
        response = await self._handle_request(command)
        columns = fields or response.pop(0)
        return self._format_response(columns, response)

    async def get_one(self, source, query_filter, fields=None):
        query = [f"GET {source}"]

        if query_filter:
            query.append(f'Filter: {query_filter}')

        if isinstance(fields, list):
            query.append(await serialize_columns(fields))

        response = await self.send(query, fields)

        if len(response) == 0:
            raise NoMatchFound()
        elif len(response) > 1:
            self.log.error(f"Query: {query} yielded multiple results")
            raise AioliException()

        return response[0]

    async def get_many(self, source, query_filter=None, fields=None):
        query = [f"GET {source}"]

        if query_filter:
            query.append(f"Filter: {query_filter}")

        if isinstance(fields, list):
            query.append(await serialize_columns(fields))

        return await self.send(query, fields)

    async def _handle_request(self, *args, **kwargs):
        # @TODO - implement connection re-use / queuing ?
        # @TODO - implement error handling :: result['failed'], ['total_count']
        # @TODO - implement stream parser

        try:
            reader, writer = await self._get_connection()
        except OSError as e:
            error_msg = str(e)
            raise AioliException(message=f"Error connecting to Livestatus: {error_msg}")

        await self._write(writer, *args, **kwargs)
        response = await self._read(reader)
        writer.close()

        return ujson.loads(response)
