import asyncio
from amqtt.broker import Broker

async def main():
    config = {
        'listeners': {
            'default': {
                'type': 'tcp',
                'bind': '0.0.0.0:1883'
            }
        }
    }
    broker = Broker(config)
    await broker.start()
    print("MQTT Broker started on port 1883")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
