import asyncio
import json
import logging
import uuid
from os import getenv as env
from typing import Awaitable, Callable, Optional

from aio_pika import DeliveryMode, Message, connect_robust
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class PikaClient:
	def __init__(self):
		self.connection = None
		self.channels = {}

	async def connect(self, retries: int = 5, delay: float = 5.0):
		for attempt in range(retries):
			try:
				self.connection = await connect_robust(
					host=env("RABBITMQ_HOST", "localhost"),
				)
				logger.info("Connected to RabbitMQ")
				return
			except Exception as e:
				logging.warning(
					f"RabbitMQ not ready (attempt {attempt + 1}/{retries}): {e}"
				)
				await asyncio.sleep(delay)

		raise RuntimeError(f"Failed to connect to RabbitMQ after {retries} attempts")

	async def _get_channel(self, name: str, prefetch_count: Optional[int] = None):
		if name not in self.channels:
			channel = await self.connection.channel()
			if prefetch_count is not None:
				await channel.set_qos(prefetch_count=prefetch_count)
			self.channels[name] = channel
		return self.channels[name]

	async def consume(
		self,
		queue_name: str,
		process_callable: Callable[[bytes], Awaitable[None]],
		prefetch_count: int = 1,
	):
		channel = await self._get_channel(queue_name, prefetch_count)
		queue = await channel.declare_queue(queue_name, durable=True)
		logger.info(f"Consuming queue={queue_name}")

		async with queue.iterator() as queue_iter:
			async for message in queue_iter:
				async with message.process():
					try:
						await process_callable(message.body)
					except ValidationError as e:
						logger.error(
							f"Invalid payload\nraw: {message.body.decode()}\nerrors: {e.errors()}",
						)
						continue

	async def publish(self, queue_name: str, payload: dict):
		channel = await self._get_channel("publisher")

		await channel.default_exchange.publish(
			Message(
				body=json.dumps(payload).encode(),
				delivery_mode=DeliveryMode.PERSISTENT,
				message_id=str(uuid.uuid4()),
			),
			routing_key=queue_name,
		)

		logger.info(f"Published message | queue={queue_name}")

	async def close(self):
		if self.connection:
			await self.connection.close()
			logger.info("RabbitMQ connection closed")
