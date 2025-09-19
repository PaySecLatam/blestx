import cmd
import asyncio
import inspect
import os
import sys
import shlex
import importlib
import readline
from core.banner import BANNER
from core.loader import iter_modules
from core.client import show_cached_chars

current_shell = None

def load_module(module_path):
    """Carga dinámicamente un módulo"""
    return importlib.import_module(module_path)

class BleSTXShell(cmd.Cmd):
    intro = BANNER + "\nEscribe 'help' para ver comandos."
    prompt = "blestx >> "
    
    def __init__(self):
        super().__init__()
        global current_shell
        current_shell = self
        self.modules = iter_modules()
        try:
            readline.set_completer_delims(' \t\n;')
            readline.parse_and_bind("tab: complete")
        except ImportError:
            pass

    def do_modules(self, arg):
        """Lista todos los módulos disponibles por categoría"""
        for cat, mod_list in self.modules.items():
            print(f"\n[{cat}]")
            width = max(len(m) for m in mod_list) + 2
            cols = 3
            for i in range(0, len(mod_list), cols):
                row = mod_list[i:i+cols]
                print("".join(m.ljust(width) for m in row))
        print()

    def do_load(self, arg):
        """Lista módulos o carga un módulo: load discovery.scan"""
        if not arg:
            for cat, mod_list in self.modules.items():
                print(f"\n[{cat}]")
                width = max(len(m) for m in mod_list) + 2
                cols = 3
                for i in range(0, len(mod_list), cols):
                    row = mod_list[i:i+cols]
                    print("".join(m.ljust(width) for m in row))
            return

        if "." not in arg:
            print("[!] Debes indicar la categoría: discovery.scan")
            return

        category, module_name = arg.split(".", 1)
        if category not in self.modules or module_name not in self.modules[category]:
            print(f"[!] Módulo {arg} no encontrado")
            return

        try:
            mod = load_module(f"modules.{category}.{module_name}")
        except Exception as e:
            print(f"[!] Error cargando módulo: {e}")
            return

        ModuleShell(mod, arg, self).cmdloop()

    def complete_load(self, text, line, begidx, endidx):
        args = line.split()
        
        if len(args) == 1 and line.endswith(' '):
            return [cat + "." for cat in self.modules.keys()]
        elif len(args) == 2 or (len(args) == 1 and not line.endswith(' ')):
            current_arg = args[1] if len(args) > 1 else args[0]
            if '.' in current_arg:
                cat, partial_mod = current_arg.split('.', 1)
                if cat in self.modules:
                    return [f"{cat}.{m}" for m in self.modules[cat] if m.startswith(partial_mod)]
                return []
            else:
                return [cat + "." for cat in self.modules.keys() if cat.startswith(current_arg)]
        return []

    def do_exit(self, arg):
        print("Saliendo de blestx...")
        return True

    def do_quit(self, arg):
        return self.do_exit(arg)

    def do_back(self, arg):
        print("Volviendo al shell principal...")
        return True

    
    do_q = do_quit
    do_b = do_back

    def do_banner(self, arg):
        print(BANNER)

class ModuleShell(cmd.Cmd):
    def __init__(self, module, name, parent_shell):
        super().__init__()
        global current_shell
        current_shell = self
        self.module = module
        self.name = name
        self.parent_shell = parent_shell
        self.prompt = f"blestx({name}) >> "
        self.options = getattr(module, "OPTIONS", {})
        try:
            readline.set_completer_delims(' \t\n;')
            readline.parse_and_bind("tab: complete")
        except ImportError:
            pass

    def do_load(self, arg):
        """Carga otro módulo desde este módulo"""
        self.parent_shell.do_load(arg)

    def complete_load(self, text, line, begidx, endidx):
        return self.parent_shell.complete_load(text, line, begidx, endidx)

    def do_options(self, arg):
        if not self.options:
            print("(Sin opciones configurables)")
            return
        print("\n🔧 Opciones del módulo:")
        print("-" * 40)
        for k, v in self.options.items():
            print(f"{k:20} = {v}")
        print("-" * 40)

    def do_set(self, arg):
        parts = arg.split()
        if len(parts) != 2:
            print("Uso: set <param> <valor>")
            return
        key, val = parts
        if key in self.options:
            if key == "mode" and val.lower() not in ("ascii", "hex"):
                print("[!] Valores válidos para 'mode': ascii, hex")
                return
            try:
                self.options[key] = type(self.options[key])(val)
            except Exception:
                self.options[key] = val
            print(f"[+] {key} ==> {self.options[key]}")
        else:
            print(f"[!] Parámetro desconocido: {key}")

    def complete_set(self, text, line, begidx, endidx):
        try:
            parts = shlex.split(line[:begidx])
        except ValueError:
            parts = line[:begidx].split()

        
        if len(parts) == 1:
            return [k for k in self.options.keys() if k.startswith(text)]
        
        elif len(parts) >= 2:
            key = parts[1]
            if key == "mode":
                return [v for v in ["ascii", "hex"] if v.startswith(text)]
        return []
    
    def do_chars(self, arg):
        """Muestra todas las características cacheadas globalmente"""
        show_cached_chars()

    def do_run(self, arg):
        run_func = getattr(self.module, "run", None)
        if not run_func:
            print("[!] El módulo no tiene función run()")
            return
        kwargs = self.options.copy()
        print("🚀 Ejecutando módulo...")
        if inspect.iscoroutinefunction(run_func):
            asyncio.run(run_func(**kwargs))
        else:
            run_func(**kwargs)

    def do_back(self, arg):
        return True
    
    def do_info(self, arg):
        """Muestra la información del módulo cargado"""
        info = getattr(self.module, "INFO", None)
        if not info:
            print("[!] Este módulo no tiene información definida.")
            return

        print("\n📖 Información del módulo")
        print("-" * 40)
        print(f"Nombre      : {info.get('name', 'N/A')}")
        print(f"Autor       : {info.get('author', 'N/A')}")
        print(f"Descripción : {info.get('description', 'N/A')}")
        print("\nOpciones:")
        opts = info.get("options", {})
        if not opts:
            print("  (Sin opciones documentadas)")
        else:
            for k, v in opts.items():
                print(f"  {k:10} : {v}")
        print("-" * 40)

    def do_exit(self, arg):
        """Salir completamente del programa"""
        print("Bye!")
        sys.exit(0)

if __name__ == "__main__":
    BleSTXShell().cmdloop()
