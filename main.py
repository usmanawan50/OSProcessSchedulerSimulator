# libraries
import tkinter as tk
from tkinter import ttk
import random
import time
import threading

# define class Process
class Process:
    # constructor
    def __init__(self, pid, priority, burst_time, resources_needed, arrival_time):
        # attributes
        self.pid = pid
        self.priority = priority
        self.burst_time = burst_time
        self.remaining_time = burst_time    # initially burst_time equals remaining time and
        self.resources_needed = resources_needed
        self.arrival_time = arrival_time
        self.start_time = None
        self.end_time = None
        self.wait_time = 0

# define class Resource Manager
class resourceManager:
    # constructor
    def __init__(self):
        # attributes
        self.total = [5]*5      # total resources = 5
        self.available = [5]*5  # total instances of each resource = 5
        self.allocation = {pid: [0]*5 for pid in range(1, 11)}  # initially no resource isnallocated

    # class methods
    ############################################################
    def request(self, pid, resources_needed):   # use Banker's algorithm to avoid deadlocks
        # check if request is safe and grant if possible
        if self._is_safe(pid, resources_needed):
            for a in range(5):  # grant resources if resources are available
                self.available[a] -= resources_needed[a]
                self.allocation[pid][a] += resources_needed[a]
            return True
        return False
    ############################################################
    def _is_safe(self, pid, request):   # helper method for the request method
        # check if granting request keeps system in safe state
        temp = self.available[:]  # store resource list in temp variable
        for a in range(5):
            if request[a] > temp[a]:  # check instances of each resource
                return False
        return True
    ############################################################
    def release(self, pid):     # release resources when execution is over
        # release all resources held by the process
        if pid in self.allocation:
            for a in range(5):
                self.available[a] += self.allocation[pid][a]
            self.allocation[pid] = [0]*5


# define class Scheduler
class Scheduler:
    # constructor
    def __init__(self, gui):
        # attributes
        self.q0 = []
        self.q1 = []
        self.q2 = []
        self.wait_queue = []
        self.resource_manager = resourceManager()
        self.completed_processes = []
        self.gui = gui
        self.time_quantum = 5
        self.pid_counter = 1
        self.running = False
        self.lock = threading.Lock()

    # class methods
    ############################################################
    def generate_processes(self):   # generate processes
        # generate 10 random processes and put them in the wait queue
        for a in range(10):
            pid = self.pid_counter  # assign id in correspondence to last used id
            priority = random.randint(0, 2)  # queue q0-q2 correspond to priority 0-2
            burst_time = random.randint(1, 10)  # max 10s

            # each process can request 2 instances of 5 different resources at max
            resources_needed = [random.randint(0, 2) for a in range(5)]

            arrival_time = time.time()  # assign current time to process

            # initialize the process
            process = Process(pid, priority, burst_time, resources_needed, arrival_time)

            # update attributes of scheduler class
            self.wait_queue.append(process)
            self.pid_counter += 1

        # update attributes of GUI class
        self.gui.update_queues()
    ############################################################
    def enqueue_processes(self):  # put processes in queue
        # move processes from wait queue to appropriate ready queues
        while self.wait_queue:  # iterate till wait queue list is not empyy
            temp_process = self.wait_queue[0]
            queue = getattr(self, f"q{temp_process.priority}") # put process in required queue
            if len(queue) < 5:  # check if queue is full
                queue.append(self.wait_queue.pop(0))
            else:
                break

        # update attributes of gui class
        self.gui.update_queues()
    ############################################################
    def start_scheduler(self):  # start OS scheduling
        if not self.running:
            self.running = True
            threading.Thread(target=self.run_scheduler).start()
    ############################################################
    def run_scheduler(self):  # schedules processes
        # main scheduler loop: executes 3 from q0, 2 from q1, 1 from q2
        while self.running:
            for q, count in zip([self.q0, self.q1, self.q2], [3, 2, 1]):
                for a in range(count):
                    if q: # if target queue is not-empty, execute its process
                        process = q.pop(0)
                        if self.resource_manager.request(process.pid, process.resources_needed):
                            self.execute_process(process)
                        else: # if target queue is empty, move to next queue
                            q.append(process)

            # update attributes of scheduler class
            self.enqueue_processes()

            # delay to avoid inconsistent behaviour
            time.sleep(1)
    ############################################################
    def execute_process(self, process):  # execute process
        # run process for up to time quantum = 5s

        self.gui.update_current_process(process) # update gui

        if process.start_time is None:  # record start time
            process.start_time = time.time()
        start = time.time()  # start time slice

        # execute process till time quantum or till it's done
        while process.remaining_time > 0 and time.time() - start < self.time_quantum:
            time.sleep(1)
            process.remaining_time -= 1
            self.gui.update_current_process(process)  # update remaining time

        if process.remaining_time <= 0:  # if process completed
            process.end_time = time.time()  # record end time
            self.completed_processes.append(process)   # append process to complete queue
            self.resource_manager.release(process.pid) # release processes resources
            self.gui.update_gantt_chart(process)       # update gantt chart
        else: # if process did not complete
            # preempt to lower priority queue
            new_priority = min(process.priority + 1, 2) # update priority according to queue
            process.priority = new_priority
            getattr(self, f"q{new_priority}").append(process)
            self.resource_manager.release(process.pid)

        # update attributes of gui class
        self.gui.update_queues()
        self.gui.update_avg_times(self.completed_processes)
        self.gui.update_resource_table(self.resource_manager)

# define class GUI
class GUI:
    # constructor
    def __init__(self, root):
        # attributes
        self.root = root
        self.root.title("OS Simulation")
        self.root.configure(bg="#f0f8ff")
        self.scheduler = Scheduler(self)
        self.setup_ui()

    # class methods
    ############################################################
    def setup_ui(self):  # gui layout
        # buttons to generate processes and start scheduler
        self.button = tk.Button(self.root, text="Generate Processes", command=self.scheduler.generate_processes, bg="#add8e6", font=("Arial", 12))
        self.button.pack(pady=5)

        self.start_button = tk.Button(self.root, text="Start Scheduler", command=self.scheduler.start_scheduler, bg="#90ee90", font=("Arial", 12))
        self.start_button.pack(pady=5)

        # queues display
        self.queues_label = tk.Label(self.root, text="Queues", font=("Arial", 14, "bold"), bg="#f0f8ff")
        self.queues_label.pack()
        self.queues_text = tk.Text(self.root, height=10, width=100, bg="#e6f7ff")
        self.queues_text.pack()

        # current process display
        self.current_process_label = tk.Label(self.root, text="Current Process", font=("Arial", 14, "bold"), bg="#f0f8ff")
        self.current_process_label.pack()
        self.current_process_text = tk.Text(self.root, height=2, width=100, bg="#fffacd")
        self.current_process_text.pack()

        # gantt chart display
        self.gantt_label = tk.Label(self.root, text="Gantt Chart", font=("Arial", 14, "bold"), bg="#f0f8ff")
        self.gantt_label.pack()

        self.gantt_text = tk.Text(self.root, height=2, width=100, bg="#ffe4e1")  # Corrected to self.gantt_text
        self.gantt_text.pack()

        # average times display
        self.average_label = tk.Label(self.root, text="Avg Turnaround and Wait Time", font=("Arial", 14, "bold"),
                                      bg="#f0f8ff")
        self.average_label.pack()

        self.avg_text = tk.Text(self.root, height=2, width=100, bg="#fafad2")  # Corrected to self.avg_text
        self.avg_text.pack()

        # Resource table display
        self.resource_label = tk.Label(self.root, text="Resource Allocation Table", font=("Arial", 14, "bold"), bg="#f0f8ff")
        self.resource_label.pack()
        self.resource_text = tk.Text(self.root, height=6, width=100, bg="#e0ffff")
        self.resource_text.pack()
    ############################################################
    def update_queues(self):  # update queue on gui
        # refresh all queues and wait queue display
        text = ""
        for a in range(3):
            queue = getattr(self.scheduler, f"q{a}")
            text += f"Queue q{a}: {[p.pid for p in queue]}\n"
        text += f"Wait Queue: {[p.pid for p in self.scheduler.wait_queue]}"
        self.queues_text.delete(1.0, tk.END)
        self.queues_text.insert(tk.END, text)
    ############################################################
    def update_current_process(self, process):  # update current process on gui
        # Display currently running process with live remaining time
        self.current_process_text.delete(1.0, tk.END)
        self.current_process_text.insert(tk.END, f"Process {process.pid}, Priority {process.priority}, Remaining {process.remaining_time}s")
    ############################################################
    def update_gantt_chart(self, process):  # update gantt chart
        # show last 5 executed processes
        self.gantt_text.insert(tk.END, f"P{process.pid} ")
        lines = self.gantt_text.get(1.0, tk.END).split()
        if len(lines) > 5:
            self.gantt_text.delete(1.0, tk.END)
            self.gantt_text.insert(tk.END, " ".join(lines[-5:]))
    ############################################################
    def update_avg_times(self, completed): # update average time on gui
        # update average turnaround and wait time display
        if not completed:
            return
        total_ta_t = sum(p.end_time - p.arrival_time for p in completed)
        total_w_t = sum(p.start_time - p.arrival_time for p in completed)
        avg_tat = total_ta_t / len(completed)
        avg_w_t = total_w_t / len(completed)
        self.avg_text.delete(1.0, tk.END)
        self.avg_text.insert(tk.END, f"Avg TAT: {avg_tat:.2f}s, Avg WT: {avg_w_t:.2f}s")
    ############################################################
    def update_resource_table(self, rm):  # update resource table on gui
        # Display current available resources and allocation table
        text = f"Available: {rm.available}\n"
        text += f"Allocations:\n"
        for pid, alloc in rm.allocation.items():
            text += f"P{pid}: {alloc}\n"
        self.resource_text.delete(1.0, tk.END)
        self.resource_text.insert(tk.END, text)

# Entry point
if __name__ == "__main__":
    root = tk.Tk()
    gui = GUI(root)
    root.mainloop()
