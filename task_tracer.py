import trio
import re
from enum import IntEnum

class FilterType(IntEnum):
    NO_FILTERS=0
    EXCLUDE=1
    INCLUDE=2
    
class Tracer(trio.abc.Instrument):
    
    filters = []
    filterType = FilterType.NO_FILTERS
    
    def addFilters(self, filterType, *filtStr):
        # filterRegex = re.compile(r"<Task \'\\S{3,}" + taskName + r"\' at 0x\\S{3,}>")
        self.filterType = filterType
        for s in filtStr:
            filterRegex = re.compile(s)
            self.filters.append(filterRegex)
    
    def taskFilter(self, task):
        matchFound = False
        if self.filterType != FilterType.NO_FILTERS:
            for filt in self.filters:
                if re.search(filt, repr(task)):
                    # Positive Match
                    if self.filterType == FilterType.EXCLUDE:
                        return None
                    elif self.filterType == FilterType.INCLUDE:
                        return task
                else:
                    # Negative Match
                    continue

            if self.filterType == FilterType.EXCLUDE:
                return task
            elif  self.filterType == FilterType.INCLUDE:
                return None
                
        else:
            return task
        
    def before_run(self):
        print("!!! run started")

    def _print_with_task(self, msg, task):
        # repr(task) is perhaps more useful than task.name in general,
        # but in context of a tutorial the extra noise is unhelpful.
        if self.taskFilter(task):
            print(f"{msg}: {task.name}")

    def task_spawned(self, task):
        if self.taskFilter(task):
            self._print_with_task("### new task spawned", task)

    def task_scheduled(self, task):
        if self.taskFilter(task):
            self._print_with_task("### task scheduled", task)

    def before_task_step(self, task):
        if self.taskFilter(task):
            self._print_with_task(">>> about to run one step of task", task)

    def after_task_step(self, task):
        if self.taskFilter(task):
            self._print_with_task("<<< task step finished", task)

    def task_exited(self, task):
        if self.taskFilter(task):
            self._print_with_task("### task exited", task)

    # def before_io_wait(self, timeout):
    #     if timeout:
    #         print(f"### waiting for I/O for up to {timeout} seconds")
    #     else:
    #         print("### doing a quick check for I/O")
    #     self._sleep_time = trio.current_time()

    # def after_io_wait(self, timeout):
    #     duration = trio.current_time() - self._sleep_time
    #     print(f"### finished I/O check (took {duration} seconds)")

    def after_run(self):
        print("!!! run finished")