# This file is part of BLEAH.
#
# Copyleft 2017 Simone Margaritelli
# evilsocket@protonmail.com
# http://www.evilsocket.net
#
# This file may be licensed under the terms of of the
# GNU General Public License Version 3 (the ``GPL'').
#
# Software distributed under the License is distributed
# on an ``AS IS'' basis, WITHOUT WARRANTY OF ANY KIND, either
# express or implied. See the GPL for the specific language
# governing rights and limitations.
#
# You should have received a copy of the GPL along with this
# program. If not, go to http://www.gnu.org/licenses/gpl.html
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
# 
# Parte de BLEAH - Adaptación para blestx

import os

FILEPATH = os.path.realpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'oui.dat')
)

VENDORS = {}

def load():
    """Carga el archivo oui.dat en el diccionario VENDORS"""
    VENDORS.clear()
    try:
        with open(FILEPATH, 'r', encoding='utf-8', errors='replace') as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    oui, name = line.split(maxsplit=1)
                    key = oui.upper().replace(":", "").replace("-", "")
                    VENDORS[key] = name.strip()
                except ValueError:
                    continue
    except FileNotFoundError:
        print(f"[!] Archivo oui.dat no encontrado en: {FILEPATH}")
    except Exception as e:
        print(f"[!] Error cargando vendors: {e}")

def find(addr):
    clean_addr = addr.replace(":", "").replace("-", "").upper()
    if len(clean_addr) < 6:
        return "unknown"
    key = clean_addr[:6]
    return VENDORS.get(key, "unknown")