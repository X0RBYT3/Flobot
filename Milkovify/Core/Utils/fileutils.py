import logging
import json
import inspect
import asyncio
import traceback
import collections

log = logging.getLogger(__name__)

class EventEmitter:
    def __init__(self):
        self._events = collections.defaultdict(list)
        self.loop = asyncio.get_event_loop()

    def emit(self, event, *args, **kwargs):
        if event not in self._events:
            return

        for cb in list(self._events[event]):
            # noinspection PyBroadException
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.ensure_future(cb(*args, **kwargs), loop=self.loop)
                else:
                    cb(*args, **kwargs)

            except:
                traceback.print_exc()

    def on(self, event, cb):
        self._events[event].append(cb)
        return self

    def off(self, event, cb):
        self._events[event].remove(cb)

        if not self._events[event]:
            del self._events[event]

        return self

    def once(self, event, cb):
        def callback(*args, **kwargs):
            self.off(event, callback)
            return cb(*args, **kwargs)

        return self.on(event, callback)

def _get_variable(name):
    stack = inspect.stack()
    try:
        for frames in stack:
            try:
                frame = frames[0]
                current_locals = frame.f_locals
                if name in current_locals:
                    return current_locals[name]
            finally:
                del frame
    finally:
        del stack

def objdiff(obj1, obj2, *, access_attr=None, depth=0):

    changes = {}

    if access_attr is None:
        attrdir = lambda x: x

    elif access_attr == 'auto':
        if hasattr(obj1, '__slots__') and hasattr(obj2, '__slots__'):
            attrdir = lambda x: getattr(x, '__slots__')

        elif hasattr(obj1, '__dict__') and hasattr(obj2, '__dict__'):
            attrdir = lambda x: getattr(x, '__dict__')

        else:
            # log.everything("{}{} or {} has no slots or dict".format('-' * (depth+1), repr(obj1), repr(obj2)))
            attrdir = dir

    elif isinstance(access_attr, str):
        attrdir = lambda x: list(getattr(x, access_attr))

    else:
        attrdir = dir

    # log.everything("Diffing {o1} and {o2} with {attr}".format(o1=obj1, o2=obj2, attr=access_attr))

    for item in set(attrdir(obj1) + attrdir(obj2)):
        try:
            iobj1 = getattr(obj1, item, AttributeError("No such attr " + item))
            iobj2 = getattr(obj2, item, AttributeError("No such attr " + item))

            if depth:

                idiff = objdiff(iobj1, iobj2, access_attr='auto', depth=depth - 1)
                if idiff:
                    changes[item] = idiff

            elif iobj1 is not iobj2:
                changes[item] = (iobj1, iobj2)

            else:
                pass

        except Exception as e:
            log.warning("Error checking {o1}/{o2}.{item}".format(o1=obj1, o2=obj2, item=item), exc_info=e)
            continue

    return changes

class Serializable:

    def __init__(self):
        """
        Unironically just to stop pycharm shitting itself
        """
        pass

    _class_signature = ('__class__', '__module__', 'data')

    def _enclose_json(self, data):
        return {
            '__class__': self.__class__.__qualname__,
            '__module__': self.__module__,
            'data': data
        }

    def serialize(self, *, cls=Serializer, **kwargs):
        return json.dumps(self, cls=cls, **kwargs)

    def __json__(self):
        raise NotImplementedError

    @classmethod
    def _deserialize(cls, raw_json, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _bad(arg):
        raise TypeError('Argument "%s" must not be None' % arg)

    @property
    def class_signature(self):
        return self._class_signature


class Serializer(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, '__json__'):
            return o.__json__()

        return super().default(o)

    @classmethod
    def deserialize(cls, data):
        if all(x in data for x in Serializable.class_signature):
            log.debug("Deserialization requested for %s", data)
            factory = pydoc.locate(data['__module__'] + '.' + data['__class__'])
            log.debug("Found object %s", factory)
            if factory and issubclass(factory, Serializable):
                log.debug("Deserializing %s object", factory)
                return factory._deserialize(data['data'], **cls._get_vars(factory._deserialize))

        return data

    @classmethod
    def _get_vars(cls, func):
        log.debug("Getting vars for %s", func)
        params = inspect.signature(func).parameters.copy()
        args = {}
        log.debug("Got %s", params)

        for name, param in params.items():
            log.debug("Checking arg %s, type %s", name, param.kind)
            if param.kind is param.POSITIONAL_OR_KEYWORD and param.default is None:
                log.debug("Using var %s", name)
                args[name] = _get_variable(name)
                log.debug("Collected var for arg '%s': %s", name, args[name])

        return args
