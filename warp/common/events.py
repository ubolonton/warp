import traceback
from collections import defaultdict

from storm.locals import Store, Storm
from storm.info import get_obj_info


handlers = defaultdict(list)

def handler(event, *models):
    if not models:
        models = [None]
    else:
        models = [model.__name__ for model in models]

    def decorate(fun):
        for modelName in models:
            handlers[(modelName, event)].append(fun)
        return fun

    return decorate



class CommitEventStore(Store):

    def __init__(self, database, cache=None):
        self.events = []
        super(CommitEventStore, self).__init__(database, cache)

    def rollback(self):
        self.events = []
        super(CommitEventStore, self).rollback()

    def commit(self):
        super(CommitEventStore, self).commit()

        # Event handlers can emit new events, which will run after
        # all existing events are handled. Do a little dance here
        # to make this clean.
        while self.events:
            events = self.events
            self.events = []
            for event in events:
                event.run()


class EventModel(Storm):
    # NTA TODO: Shouldn't skip_duplicate default to True?
    def emit(self, event, skip_duplicate=False, **kwargs):
        """Emits an event to be run when the model's associated store
        commits. Handlers will be called like handler(model, **kwargs).

        Does nothing if \"skip_duplicate\" is True, and an \"identical\"
        event was already emitted."""

        store = get_obj_info(self)["store"]
        if store is None:
            raise Exception("Tried to emit event for store-less object")

        if skip_duplicate:
            for pending in store.events:
                # NTA XXX: Equality in Python is unreliable
                if pending.obj == self and pending.event == event and pending.kwargs == kwargs:
                    return

        store.events.append(PendingEvent(self, event, kwargs))


class PendingEvent(object):
    def __init__(self, obj, event, kwargs=None):
        self.obj = obj
        self.event = event
        self.kwargs = kwargs

    def run(self):
        modelName = self.obj.__class__.__name__
        eventHandlers = (set(handlers.get((modelName, self.event), []))
                         | set(handlers.get((None, self.event), [])))

        for handler in eventHandlers:
            try:
                handler(self.obj, **self.kwargs)
            except Exception:
                print ">>> Error in event handler"
                traceback.print_exc()
