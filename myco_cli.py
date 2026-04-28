import requests
import sys

BASE = "http://localhost:8000"

def seed():
    r = requests.post(f"{BASE}/seed")
    print(r.json())

def state():
    r = requests.get(f"{BASE}/organism")
    data = r.json()
    print(f"\n=== CHARTER ===")
    print(f"Mission: {data['charter']['mission']}")
    print(f"Seed: ${data['charter']['seed_capital']}")
    print(f"\n=== AGENTS ({data['financials']['active_agents']}) ===")
    for a in data['agents']:
        print(f"  {a['agent_id']:22} | {a['name']:10} | ${a['wallet']:>7.1f} | rep:{a['reputation']} | {a['status']}")
    print(f"\n=== JOBS ({len(data['open_jobs'])} open) ===")
    for j in data['open_jobs']:
        print(f"  {j['job_id']:22} | ${j['budget']:>6} | {j['description'][:50]}")
    print(f"\n=== P&L ===")
    print(f"  Tax collected: ${data['financials']['total_tax_collected']}")
    print(f"  Agent wealth:  ${data['financials']['agent_wealth_total']}")

def execute(agent_id, task):
    r = requests.post(f"{BASE}/agents/{agent_id}/execute", json={
        "task": task,
        "context": ""
    })
    data = r.json()
    print(f"\n=== AGENT {agent_id} OUTPUT ===")
    print(data.get('output', 'ERROR'))

def scan():
    r = requests.post(f"{BASE}/opportunities/scan")
    print(r.json())

def bid(job_id, agent_id, price):
    r = requests.post(f"{BASE}/jobs/{job_id}/bid", json={
        "agent_id": agent_id,
        "price": price
    })
    print(r.json())

def complete(job_id, deliverable):
    r = requests.post(f"{BASE}/jobs/{job_id}/complete", json={
        "deliverable": deliverable,
        "rating": 5
    })
    print(r.json())

def pnl():
    r = requests.get(f"{BASE}/ledger/pnl")
    print(r.json())

def model_info():
    r = requests.get(f"{BASE}/system/model")
    print(r.json())

def auto_cycle():
    r = requests.post(f"{BASE}/autonomy/cycle")
    print(r.json())

def auto_detect(agent_id, task):
    r = requests.post(f"{BASE}/autonomy/detect", json={
        "agent_id": agent_id,
        "task_description": task
    })
    print(r.json())

def auto_publish(agent_id, need, budget):
    r = requests.post(f"{BASE}/autonomy/publish", json={
        "agent_id": agent_id,
        "need_description": need,
        "budget": budget
    })
    print(r.json())

def auto_bid(job_id):
    r = requests.post(f"{BASE}/autonomy/bid/{job_id}")
    print(r.json())

def auto_complete(job_id):
    r = requests.post(f"{BASE}/autonomy/complete/{job_id}")
    print(r.json())

def improve(agent_id, task, output, feedback=None, rating=None):
    payload = {
        "agent_id": agent_id,
        "task": task,
        "output": output,
        "feedback": feedback,
        "rating": rating
    }
    r = requests.post(f"{BASE}/improvement/evaluate", json=payload)
    print(r.json())

def exec_skills(agent_id, task):
    r = requests.post(f"{BASE}/improvement/execute-with-skills", json={
        "agent_id": agent_id,
        "task": task
    })
    print(r.json())

def list_skills(agent_id):
    r = requests.get(f"{BASE}/improvement/skills/{agent_id}")
    print(r.json())

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "state"
    if cmd == "seed": seed()
    elif cmd == "state": state()
    elif cmd == "scan": scan()
    elif cmd == "pnl": pnl()
    elif cmd == "model": model_info()
    elif cmd == "cycle": auto_cycle()
    elif cmd == "detect" and len(sys.argv) > 3: auto_detect(sys.argv[2], sys.argv[3])
    elif cmd == "publish" and len(sys.argv) > 4: auto_publish(sys.argv[2], sys.argv[3], float(sys.argv[4]))
    elif cmd == "autobid" and len(sys.argv) > 2: auto_bid(sys.argv[2])
    elif cmd == "autocomplete" and len(sys.argv) > 2: auto_complete(sys.argv[2])
    elif cmd == "execute" and len(sys.argv) > 3: execute(sys.argv[2], sys.argv[3])
    elif cmd == "bid" and len(sys.argv) > 4: bid(sys.argv[2], sys.argv[3], float(sys.argv[4]))
    elif cmd == "complete" and len(sys.argv) > 3: complete(sys.argv[2], sys.argv[3])
    elif cmd == "improve" and len(sys.argv) > 4: improve(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else None)
    elif cmd == "skills" and len(sys.argv) > 2: list_skills(sys.argv[2])
    elif cmd == "execskills" and len(sys.argv) > 3: exec_skills(sys.argv[2], sys.argv[3])
    else:
        print("Commands:")
        print("  === SEMANA 1: Manual ===")
        print("  seed                          - Plant initial charter + agents")
        print("  state                         - Full organism status")
        print("  scan                          - Kernel scans for opportunities")
        print("  pnl                           - Profit & Loss")
        print("  model                         - Current AI provider info")
        print("  execute <agent_id> '<task>'   - Run task via AI")
        print("  bid <job_id> <agent_id> <price> - Bid on open job")
        print("  complete <job_id> '<result>'    - Complete job, get paid")
        print("  === SEMANA 2: Autonomy ===")
        print("  cycle                         - Run full auto-contratacion cycle")
        print("  detect <agent_id> '<task>'    - Agent detects skill gap & publishes job")
        print("  publish <agent_id> '<need>' <budget> - Agent publishes job with own wallet")
        print("  autobid <job_id>              - Auto-bid on open job")
        print("  autocomplete <job_id>         - Auto-execute & complete assigned job")
        print("  === SEMANA 3: Karpathy Loop ===")
        print("  improve <agent_id> '<task>' '<output>' ['<feedback>'] - Evaluate & generate skill")
        print("  skills <agent_id>             - List agent's learned skills")
        print("  execskills <agent_id> '<task>' - Execute using learned skills first")
