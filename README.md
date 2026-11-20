# NOVA SmartHome

### Nagy nyelvi modell által vezérelt okosotthon Cisco Packet Tracer környezetben

**AI-alapú okosotthon-vezérlő rendszer Cisco Packet Tracer integrációval**

---

## Áttekintés

A NOVA SmartHome egy Python nyelven fejlesztett, mesterséges intelligencián alapuló okosotthon-vezérlő alkalmazás, amely természetes nyelvű utasítások segítségével képes a Cisco Packet Tracerben található IoT-eszközök vezérlésére.

A rendszer egy helyben futó **Qwen3.5:4B** nyelvi modellt használ az **Ollama** segítségével, így az AI-feldolgozáshoz nincs szükség felhőalapú API-szolgáltatásra.

## Bemutató

*A NOVA SmartHome működését bemutató képernyőkép helye.*

---

## Főbb funkciók

- **Természetes nyelvi feldolgozás:** magyar nyelvű utasítások értelmezése
- **Helyi AI-modell:** Qwen3.5:4B
- **Szimulációs környezet:** Cisco Packet Tracer 8.2.1
- **Automatikus eszközfelismerés:** elérhető IoT-eszközök azonosítása
- **Eszközvezérlés:** PTMP / IPC kommunikáción keresztül
- **Többlépéses utasítások:** több művelet végrehajtása egyetlen kérésből
- **Állapotellenőrzés:** eszközállapotok lekérdezése és ellenőrzése
- **Strukturált döntéshozatal:** JSON-alapú AI-döntések
- **Parancsvalidáció:** Python-oldali műveletellenőrzés
- **Terminálfelület:** interaktív, Rich-alapú megjelenítés

## Támogatott eszközök

| Eszköz | Műveletek |
|---|---|
| **Lámpa** | Be- és kikapcsolás |
| **Ventilátor** | Kikapcsolás, alacsony és magas fokozat |
| **Ajtó** | Nyitás, csukás, zárás, feloldás |
| **Ablak** | Nyitás és csukás |
| **Kávéfőző** | Be- és kikapcsolás (integráció alatt) |

A rendszer moduláris felépítésének köszönhetően további IoT-eszközökkel bővíthető.

---

## Rendszerarchitektúra

```text
Felhasználó
    |
    v
NOVA Terminal
    |
    v
SmartHome AI Agent
    |
    v
Ollama / Qwen3.5:4B
    |
    v
JSON műveletterv
    |
    v
Python DeviceTools
    |
    v
PTMP / IPC Client
    |
    v
Cisco Packet Tracer
    |
    v
IoT-eszközök
```

Az AI feladata a felhasználói utasítások értelmezése és a megfelelő eszközműveletek kiválasztása. A műveleteket a Python alkalmazás ellenőrzi, majd a Cisco Packet Tracer felé továbbítja.

---

## Követelmények

A rendszer futtatásához az alábbi szoftverek és komponensek szükségesek:

| Komponens | Követelmény |
|---|---|
| **Operációs rendszer** | Windows 10 / Windows 11 |
| **Python** | 3.12 |
| **Cisco Packet Tracer** | 8.2.1 |
| **AI-futtatókörnyezet** | Ollama |
| **Nyelvi modell** | Qwen3.5:4B |
| **Kommunikáció** | Engedélyezett és megfelelően konfigurált Cisco IPC-kapcsolat |

---

## Telepítés és indítás

### 1. AI-modell letöltése

```powershell
ollama pull qwen3.5:4b
```

### 2. Python virtuális környezet létrehozása

```powershell
python -m venv .venv
```

### 3. Függőségek telepítése

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install rich
```

### 4. Cisco Packet Tracer konfigurálása

A Packet Tracerben engedélyezni és regisztrálni kell a NOVA SmartHome külső alkalmazást (ExApp).

**Alkalmazásazonosító:**

```text
hu.nova.smarthome
```

A regisztrált alkalmazás hitelesítési kulcsát környezeti változóként kell megadni.

**PowerShell:**

```powershell
$env:NOVA_PT_PASSWORD = "SAJAT_IPC_KULCS"
```

> **Biztonsági megjegyzés:** A tényleges hitelesítési kulcsot ne töltsd fel a GitHub-repositoryba.

### 5. NOVA indítása

```powershell
.\.venv\Scripts\python.exe nova_terminal.py
```

**Alternatív terminálos teszt:**

```powershell
.\.venv\Scripts\python.exe -m tests.test_ai_device
```

---

## Példautasítások

A NOVA természetes magyar nyelvű utasításokkal vezérelhető.

```text
Kapcsold fel a lámpát!

Indítsd el a ventilátort!

Állítsd a ventilátort maximális fokozatra!

Nyisd ki a hálószoba ablakát!

Csukd be mindkét ablakot!

Nyisd ki a bejárati ajtót!

Kapcsold le a lámpát és állítsd le a ventilátort!
```

---

## Felhasznált technológiák

| Technológia | Szerepe |
|---|---|
| **Python** | Alkalmazáslogika és eszközvezérlés |
| **Qwen3.5:4B** | Természetes nyelvű utasítások értelmezése |
| **Ollama** | Helyi AI-modell futtatása |
| **Cisco Packet Tracer** | IoT-eszközök szimulációja |
| **PTMP / IPC** | Kommunikáció a Packet Tracerrel |
| **Rich** | Interaktív terminálfelület
