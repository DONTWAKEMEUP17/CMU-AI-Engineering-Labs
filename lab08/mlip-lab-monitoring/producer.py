import time, random, datetime
from kafka import KafkaProducer

TOPIC = 'movielog'
producer = KafkaProducer(bootstrap_servers='localhost:9092')
MOVIES = ['the+matrix+1999', 'inception+2010', 'interstellar+2014',
          'parasite+2019', 'whiplash+2014', 'arrival+2016']

def make_event():
    ts  = datetime.datetime.now().isoformat()
    uid = random.randint(1, 999999)
    status  = random.choices([200, 200, 200, 200, 400, 500], k=1)[0] 
    recs    = ', '.join(random.sample(MOVIES, 3))
    latency = random.randint(20, 800)  # ms
    return f"{ts},{uid},recommendation request 17645-team01:8082, status {status}, result: {recs}, {latency} ms"

print(f"Producing fake movielog events to '{TOPIC}'... Ctrl-C to stop")
while True:
    producer.send(TOPIC, make_event().encode('utf-8'))
    time.sleep(random.uniform(0.2, 1.0))