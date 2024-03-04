from abc import abstractmethod
from typing import Optional, Iterable, Type, TypeVar

from hyperstone.emulator import HyperEmu
from hyperstone.util import log

IMPORTED_PLUGIN_NAME = 'HYPERSTONE_REQUIRE__{name}_'


class Plugin:
    _INTERACT_TYPE = TypeVar('_INTERACT_TYPE')
    _PLUGIN_TYPE = TypeVar('_PLUGIN_TYPE', bound='Plugin')

    @property
    def plugin_name(self) -> str:
        return type(self).__name__

    def __init__(self):
        self._interact_queue = []
        self.emu: Optional[HyperEmu] = None

    @property
    def ready(self) -> bool:
        return self.emu is not None

    def prepare(self, emu: HyperEmu):
        if self.ready:
            return

        self.emu = emu
        self._handle_interact(*self._interact_queue)
        self._interact_queue.clear()

    def interact(self, *objs: '_INTERACT_TYPE'):
        if self.ready:
            self._handle_interact(*objs)
        else:
            self._interact_queue += objs

    @abstractmethod
    def _handle_interact(self, *objs: '_INTERACT_TYPE'):
        pass

    @staticmethod
    def require(plugin: Type[_PLUGIN_TYPE], emu: HyperEmu) -> _PLUGIN_TYPE:
        for loaded in Plugin.get_all_loaded(plugin, emu):
            return loaded
        new_plug: Plugin = plugin()

        if isinstance(emu.settings, list):
            emu.settings.append(new_plug)
        else:
            setattr(emu.settings, IMPORTED_PLUGIN_NAME.format(name=plugin.__name__), new_plug)

        new_plug.prepare(emu)
        return new_plug

    @staticmethod
    def get_all_loaded(plugin: Type[_PLUGIN_TYPE], emu: HyperEmu) -> Iterable[_PLUGIN_TYPE]:
        for has_plugin in emu.settings:
            if has_plugin.plugin_name == plugin.__name__:
                yield has_plugin


class RunnerPlugin(Plugin):
    def run(self):
        if not self.ready:
            log.error('Attempted to call run too early!')
        else:
            self._run()

    @abstractmethod
    def _run(self):
        pass
