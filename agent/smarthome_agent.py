
import json
import os
import urllib.error
import urllib.request

from tools.device_tools import DeviceTools


class SmartHomeAgent:
    STATE_ALIASES = {
        "Light": {
            "on": "on",
            "off": "off",
            "enabled": "on",
            "disabled": "off",
        },
        "Fan": {
            "on": "low",
            "off": "off",
            "slow": "low",
            "medium": "low",
            "normal": "low",
            "fast": "high",
            "max": "high",
            "maximum": "high",
        },
        "Door": {
            "opened": "open",
            "closed": "close",
            "locked": "lock",
            "unlocked": "unlock",
        },
        "Window": {
            "on": "open",
            "off": "close",
            "opened": "open",
            "closed": "close",
        },
        "Coffee Maker": {
            "on": "on",
            "off": "off",
        },
        "Coffee Pot": {
            "on": "on",
            "off": "off",
        },
    }

    DEVICE_ACTIONS = {
        "Light": ["on", "off"],
        "Fan": ["off", "low", "high"],
        "Door": ["open", "close", "lock", "unlock"],
        "Window": ["open", "close"],
        "Coffee Maker": ["on", "off"],
        "Coffee Pot": ["on", "off"],
    }

    DEVICE_LOCATIONS = {
        "IoT2": "nappali",
        "IoT3": "hálószoba",
    }

    def __init__(self, model=None, tools=None):
        self.model = model or os.getenv("NOVA_MODEL", "qwen3.5:4b")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.tools = tools if tools is not None else DeviceTools()

    def _normalize_state(self, model, state):
        normalized = str(state).strip().lower()
        return self.STATE_ALIASES.get(model, {}).get(normalized, normalized)

    def _get_actions(self, device):
        actions = device.get("actions")

        if isinstance(actions, list) and actions:
            return actions

        return self.DEVICE_ACTIONS.get(device.get("model"), [])

    def _get_location(self, device):
        return self.DEVICE_LOCATIONS.get(device.get("id"))

    def _get_available_devices(self, devices):
        available = []

        for device in devices:
            device_id = device.get("id")
            model = device.get("model")

            if not device_id:
                continue

            if device.get("controllable") is not True:
                continue

            actions = self._get_actions(device)

            if not actions:
                continue

            available.append({
                "id": device_id,
                "model": model,
                "location": self._get_location(device),
                "state": device.get("state"),
                "actions": actions,
                "controllable": True,
            })

        return available

    def _ask_model(self, message, devices):
        available_devices = self._get_available_devices(devices)

        system_prompt = """
Te NOVA vagy, egy intelligens, magyar nyelvű okosotthon-asszisztens.

Feladatod a felhasználó természetes nyelvű utasításainak értelmezése,
a megfelelő okosotthon-eszközök kiválasztása és a szükséges műveletek megtervezése.

A felhasználó NEM informatikus.
Természetes magyar nyelven beszél hozzád.
Nem ismeri az eszközazonosítókat, a Packet Tracert vagy a belső parancsokat.

ESZKÖZAZONOSÍTÁS:
1. A felhasználótól SOHA ne kérj IoT-eszközazonosítót.
2. Az eszközazonosítót mindig az aktuális eszközlistából válaszd ki.
3. A felhasználó természetes nyelven nevezi meg az eszközt.
4. Ha pontosan egy megfelelő típusú eszköz van, automatikusan azt válaszd.
5. Ha több megfelelő eszköz van, a helyiség alapján válassz.
6. Ha több eszköz közül nem dönthető el, melyiket szeretné,
   kérdezz vissza természetes magyar nyelven.
7. Ne találj ki eszközöket vagy azonosítókat.
8. Csak controllable=true eszközöket használhatsz.
9. Csak az adott eszköz actions listájában szereplő műveleteket választhatod.

ESZKÖZNEVEK:
- Light = lámpa, világítás, fény, villany.
- Fan = ventilátor, venti, légkeverő.
- Door = ajtó, bejárati ajtó, ajtózár.
- Window = ablak, szellőztető ablak.
- Coffee Maker = kávéfőző, kávégép, kávéautomata.
- Coffee Pot = kávéfőző, kávégép, kávéautomata.
- Air Conditioner = klíma, légkondi.
- Thermostat = termosztát, hőfokszabályzó.

A magyar ragozásokat és az ékezet nélküli szöveget is értsd meg.

PÉLDÁK A FELHASZNÁLÓI NYELVRE:
- "Kapcsold le lampat" = kapcsold ki a lámpát.
- "Nyisd ki a haloszobai ablakot" = hálószobai ablak kinyitása.
- "Fozz egy kavet" = kávéfőző bekapcsolása.
- "Kapcosld be a kavefozot" = kávéfőző bekapcsolása.
- "Meleg van, inditsd el a ventit" = ventilátor bekapcsolása.
- "Zard be az ajtot" = az ajtó becsukása és bezárása,
  ha a felhasználó egyértelműen a zár bezárását is kéri.

FONTOS:
A felhasználó nem köteles megadni az eszköz nevét pontosan.
A felhasználó nem köteles megadni az eszköz azonosítóját.
A "Főzz egy kávét" utasítás egyértelmű kávéfőző-bekapcsolási kérés,
ha pontosan egy vezérelhető kávéfőző szerepel az eszközlistában.

LÁMPA:
- on = bekapcsolás.
- off = kikapcsolás.
- "Kapcsold fel a lámpát" -> on.
- "Kapcsold le a világítást" -> off.

VENTILÁTOR:
- off = kikapcsolás.
- low = alacsony fokozat.
- high = magas fokozat.
- A ventilátor nem támogatja az on műveletet.
- "Kapcsold be a ventilátort" -> low.
- "Indítsd el a ventit" -> low.
- "Meleg van, kapcsold be a ventilátort" -> low.
- "Pörgesd fel maximumra" -> high, ha egyértelműen a ventilátorról van szó.
- "Lassítsd le a ventilátort" -> low.
- "Kapcsold ki a ventilátort" -> off.

AJTÓ:
- open = fizikailag kinyitja az ajtót.
- close = fizikailag becsukja az ajtót.
- lock = bezárja a zárat.
- unlock = kioldja a zárat.

AJTÓSZABÁLYOK:
- Ha az ajtó bezárt és ki kell nyitni, először unlock, majd open.
- Ha az ajtót be kell csukni és bezárni, először close, majd lock.
- A close és lock külön műveletek.
- Ha csak a zár kioldását kérik, csak unlock műveletet használj.
- Ha csak az ajtó becsukását kérik, ne zárd automatikusan kulcsra.

ABLAK:
- open = ablak kinyitása.
- close = ablak becsukása.
- Az ablaknak nincs lock vagy unlock művelete.

ABLAKOK HELYISÉGEI:
- IoT6 = nappali ablaka.
- IoT7 = hálószoba ablaka.

PÉLDÁK:
- "Nyisd ki a nappali ablakát" -> IoT6 open.
- "Csukd be a hálószoba ablakát" -> IoT7 close.
- "Nyisd ki mindkét ablakot" -> IoT6 open és IoT7 open.
- "Csukd be az összes ablakot" -> minden elérhető Window close.
- "Szellőztess a nappaliban" -> IoT6 open.
- "Szellőztess a hálószobában" -> IoT7 open.
- Ha csak annyit mondanak, hogy "nyisd ki az ablakot",
  és több ablak van, kérdezd meg, melyik helyiségben.

KÁVÉFŐZŐ:
- on = kávéfőző bekapcsolása.
- off = kávéfőző kikapcsolása.
- "Főzz egy kávét" -> on.
- "Indítsd el a kávéfőzőt" -> on.
- "Kapcsold be a kávéfőzőt" -> on.
- "Kapcsold ki a kávéfőzőt" -> off.
- "Készíts nekem egy kávét" -> on.
- A kávéfőző bekapcsolása nem garantálja, hogy elkészült a kávé.
- A Coffee Maker vagy Coffee Pot modellnevű eszközt használd.
- Ne kérj azonosítót, ha egyetlen kávéfőző található a listában.

KÖRNYEZETI KONTEXTUS:
- "Sötét van" -> lámpa bekapcsolása, ha egyértelmű.
- "Meleg van, kapcsold be a ventilátort" -> Fan low.
- "Szellőztess a nappaliban" -> nappali Window open.
- "Főzz egy kávét" -> kávéfőző on.
- Ha egy kérés több eszközt érint, minden műveletet külön adj meg.
- Ne válassz önkényesen több lehetséges eszköz közül.

TÖBB MŰVELET:
- Egy felhasználói utasítás több egymást követő műveletet igényelhet.
- Minden művelet külön objektum legyen az actions listában.
- A műveleteket a végrehajtás helyes sorrendjében add meg.
- Ha egy műveletnek előfeltétele van, azt is vedd figyelembe.

VÁLASZFORMÁTUM:
{
  "actions": [
    {
      "device_id": "IoT6",
      "state": "open"
    }
  ],
  "message": "Kinyitom a nappali ablakát."
}

HA NEM VÉGREHAJTHATÓ:
{
  "actions": [],
  "message": "Nem találok elérhető kávéfőzőt."
}

Ha a kérés nem egyértelmű, az actions lista legyen üres,
a message mezőben pedig természetes magyar nyelven kérj pontosítást.

Kizárólag érvényes JSON-objektummal válaszolj.
"""

        schema = {
            "type": "object",
            "properties": {
                "actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "device_id": {"type": "string"},
                            "state": {"type": "string"},
                        },
                        "required": ["device_id", "state"],
                        "additionalProperties": False,
                    },
                },
                "message": {"type": "string"},
            },
            "required": ["actions", "message"],
            "additionalProperties": False,
        }

        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": schema,
            "options": {
                "temperature": 0,
            },
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": (
                        "ELÉRHETŐ ESZKÖZÖK:\n"
                        f"{json.dumps(available_devices, ensure_ascii=False)}\n\n"
                        "FELHASZNÁLÓI UTASÍTÁS:\n"
                        f"{message}"
                    ),
                },
            ],
        }

        request = urllib.request.Request(
            f"{self.ollama_url.rstrip('/')}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as error:
            raise RuntimeError(f"Ollama connection failed: {error}") from error

        content = result.get("message", {}).get("content", "").strip()

        if not content:
            thinking = result.get("message", {}).get("thinking", "")
            done_reason = result.get("done_reason", "unknown")
            raise ValueError(
                f"Ollama returned empty content. Done reason: {done_reason}. "
                f"Thinking: {thinking[:300]}"
            )

        try:
            decision = json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid AI response: {content}") from error

        if not isinstance(decision, dict):
            raise ValueError("AI response must be a JSON object")

        actions = decision.get("actions")

        if not isinstance(actions, list):
            raise ValueError("AI response must contain an actions list")

        if len(actions) > 10:
            raise ValueError("Too many actions in AI response")

        return decision

    def _validate_actions(self, actions, devices):
        available = {
            device["id"]: device
            for device in devices
            if device.get("id") and device.get("controllable") is True
        }

        validated = []

        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                raise ValueError(f"Invalid action at index {index}")

            device_id = action.get("device_id")

            if not isinstance(device_id, str):
                raise ValueError("Invalid device ID")

            device = available.get(device_id)

            if device is None:
                raise ValueError(f"Device is not controllable: {device_id}")

            raw_state = action.get("state")

            if not isinstance(raw_state, str):
                raise ValueError("Invalid device state")

            state = self._normalize_state(device.get("model"), raw_state)
            allowed_actions = self._get_actions(device)

            if state not in allowed_actions:
                raise ValueError(
                    f"Unsupported state '{state}' for device '{device_id}'"
                )

            validated.append({
                "device_id": device_id,
                "state": state,
                "model": device.get("model"),
            })

        return validated

    def _prepare_actions(self, actions, devices):
        device_map = {
            device["id"]: device
            for device in devices
            if device.get("id")
        }

        prepared = []
        simulated_states = {}

        for action in actions:
            device_id = action["device_id"]
            state = action["state"]
            model = action["model"]

            if model != "Door":
                prepared.append(action)
                continue

            if device_id not in simulated_states:
                current = device_map[device_id].get("state")

                if not isinstance(current, dict):
                    current = {}

                simulated_states[device_id] = {
                    "door": current.get("door"),
                    "lock": current.get("lock"),
                }

            current = simulated_states[device_id]

            if state == "open":
                if current["lock"] != "0":
                    prepared.append({
                        "device_id": device_id,
                        "state": "unlock",
                        "model": model,
                    })
                    current["lock"] = "0"

                prepared.append(action)
                current["door"] = "1"

            elif state == "lock":
                if current["door"] != "0":
                    prepared.append({
                        "device_id": device_id,
                        "state": "close",
                        "model": model,
                    })
                    current["door"] = "0"

                prepared.append(action)
                current["lock"] = "1"

            elif state == "unlock":
                prepared.append(action)
                current["lock"] = "0"

            elif state == "close":
                prepared.append(action)
                current["door"] = "0"

            else:
                prepared.append(action)

        return prepared

    def _execute_actions(self, actions):
        results = []

        for action in actions:
            device_id = action["device_id"]
            state = action["state"]

            result = self.tools.set_device_state(device_id, state)

            results.append({
                "device_id": device_id,
                "action": state,
                "success": result.get("success", False),
                "result": result,
            })

            if not result.get("success"):
                return {
                    "success": False,
                    "message": (
                        f"Nem sikerült végrehajtani a(z) '{state}' "
                        f"műveletet a(z) '{device_id}' eszközön."
                    ),
                    "results": results,
                    "details": result.get("error"),
                }

        return {"success": True, "results": results}

    def process(self, message: str) -> dict:
        discovery = self.tools.list_devices()

        if not discovery.get("success"):
            return {
                "success": False,
                "message": "Nem sikerült lekérdezni az eszközöket.",
                "details": discovery.get("error"),
            }

        devices = discovery.get("devices", [])

        try:
            decision = self._ask_model(message, devices)
            actions = decision.get("actions", [])

            validated = self._validate_actions(actions, devices)

            if not validated:
                return {
                    "success": True,
                    "action": "none",
                    "actions": [],
                    "message": decision.get(
                        "message",
                        "Nem szükséges művelet."
                    ),
                }

            prepared = self._prepare_actions(validated, devices)
            execution = self._execute_actions(prepared)

            if not execution["success"]:
                return {
                    "success": False,
                    "actions": prepared,
                    "message": execution["message"],
                    "details": execution.get("details"),
                    "results": execution["results"],
                }

            responses = {
                "on": "Bekapcsoltam az eszközt.",
                "off": "Kikapcsoltam az eszközt.",
                "low": "Alacsony fokozatra állítottam a ventilátort.",
                "high": "Magas fokozatra állítottam a ventilátort.",
                "open": "Kinyitottam az eszközt.",
                "close": "Becsuktam az eszközt.",
                "lock": "Bezártam az ajtó zárját.",
                "unlock": "Kioldottam az ajtó zárját.",
            }

            if len(prepared) == 1:
                response = responses.get(
                    prepared[0]["state"],
                    "A művelet sikeresen végrehajtva."
                )
            else:
                response = "Sikeresen végrehajtottam az összes kért műveletet."

            return {
                "success": True,
                "actions": prepared,
                "results": execution["results"],
                "message": response,
            }

        except (ValueError, RuntimeError, TypeError) as error:
            return {
                "success": False,
                "message": "Nem sikerült értelmezni vagy végrehajtani az utasítást.",
                "details": str(error),
            }
