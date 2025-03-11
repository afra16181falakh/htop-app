from flask import Flask, render_template_string
import psutil
import datetime
import platform
import os

app = Flask(__name__)

def get_top_info():
    """Gets system information similar to htop."""

    uptime_seconds = int(psutil.boot_time())
    uptime = datetime.datetime.fromtimestamp(uptime_seconds)
    uptime_str = (datetime.datetime.now() - uptime).total_seconds()

    days, remainder = divmod(uptime_str, 86400)  
    hours, remainder = divmod(remainder, 3600)   
    minutes, seconds = divmod(remainder, 60)
    uptime_formatted = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

    num_cpus = psutil.cpu_count()
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    try:
        loadavg = os.getloadavg()
    except AttributeError:
        loadavg = (0.0, 0.0, 0.0)  

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time', 'status']):
        try:
            pinfo = proc.info
           
            if None not in pinfo.values():
                processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  
    processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)[:20]  # Get top 20

    process_lines = []
    for p in processes:
        create_time = datetime.datetime.fromtimestamp(p['create_time']).strftime('%H:%M:%S')
        process_lines.append(
           f"{p['pid']:>5} {p['username']:<10} {p['cpu_percent']:>5.1f} {p['memory_percent']:>5.1f} {create_time} {p['name']}"
        )
    process_table = "\n".join(process_lines)

    output = f"""
Name: Afra Falakh  
user: {os.getenv('USER', 'N/A')}
Server Time (IST): {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S.%f')}
TOP output:

top - {uptime_formatted} up,  {len(processes)} processes:  {sum(1 for p in processes if p['status'] == 'running')} running, {sum(1 for p in processes if p['status'] == 'sleeping')} sleeping, 0 stopped, {sum(1 for p in processes if p['status'] == 'zombie')} zombie
%Cpu(s):  {', '.join(f'{p:.1f}' for p in cpu_percent)}
MiB Mem : {mem.total / (1024*2):.1f} total,  {mem.free / (10242):.1f} free,  {mem.used / (10242):.1f} used,   {mem.buffers / (1024*2):.1f} buff/cache
MiB Swap: {swap.total / (1024*2):.1f} total,  {swap.free / (10242):.1f} free,  {swap.used / (10242):.1f} used.  {swap.sin / (1024*2):.1f} avail Mem

{'PID':>5} {'USER':<10} {'%CPU':>5} {'%MEM':>5} {'TIME+':>8} COMMAND
{process_table}
"""
    return output


@app.route('/htop')
def htop_endpoint():
    top_data = get_top_info()
    return f"<pre>{top_data}</pre>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
