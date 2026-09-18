# UE 5.4.4 Black Frames Diagnostic Report

**Project:** `D:\UnrealProjects\TaiWei_Cinema`  
**Target Map:** `/Game/TaiWei_Assets/TaiWei_MainScene`  
**Hardware:** NVIDIA GeForce MX450 (2GB VRAM, Driver 512.13, SM5)  
**Date:** 2026-09-12  

---

## 1. Executive Summary & Verdict
- **Status:** In Progress
- **Primary Root Cause:** [TBD]
- **Key Evidence:** [TBD]

---

## 2. Hypothesis Matrix & Experimental Verdicts

| Hypothesis | Description | Test Method | Status / Verdict | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **A. Shader Compilation Stall / XGE Hang** | Shaders pending compilation indefinitely (XGE or ShaderCompileWorker hung). Geometry renders black / default uncompiled. | Log analysis, process check, worker inspection | **Pending** | |
| **B. Corrupt DDC (DerivedDataCache)** | Corrupted DDC or Intermediate folder causing shader fetch failure or invalid bytecode. | DDC inspection & clean cache test | **Pending** | |
| **C. Project/Engine-Level Rendering Failure** | DefaultEngine.ini rendering settings or global RHI failure affecting all scenes. | Control experiment (blank level + basic cube + unlit/lit red material + Movable light) | **Pending** | |
| **D. Driver / SM5 / RHI Capability Issue** | Driver 512.13 bug or SM5 pipeline crash on MX450. | Log / crash / D3D device state analysis | **Pending** | |
| **E. Scene / Geometry / Transform Specifics** | Bounding box, mesh scale, normals, or asset setup specific to TaiWei_MainScene. | Control vs MainScene comparison | **Pending** | |

---

## 3. Log & Environment Inspection (Step 0)

### 3.1 Shader Compilation & Worker Status (Suspect A)
- **Log Source:** `D:\UnrealProjects\TaiWei_Cinema\Saved\Logs\TaiWei_Cinema.log`
- **XGE / Incredibuild:** `LogXGEController: Cannot use XGE Controller as Incredibuild is not installed on this machine.` — UE automatically fell back to Local Shader Compiler.
- **Local Compiler:** `LogShaderCompilers: Display: Using Local Shader Compiler with 5 workers.`
- **Autogen Headers:** `Autogen file is unchanged, skipping write.`
- **Active Workers in Task Manager:** 0 active `ShaderCompileWorker.exe` processes running.
- **Shader Compile Hang / Errors:** No shader compile worker crashes, no hung compilation warnings, no shader worker exceptions found in log.
- **Verdict for Suspect A (Stall/Hang):** Preliminary **ELIMINATED**. Shaders are not hung in an infinite compilation loop or dead XGE queue.

### 3.2 GPU & RHI Status (Suspect D)
- **GPU:** NVIDIA GeForce MX450, 1050 MiB / 2048 MiB used, temperature 76°C, no TDR, no throttling errors.
- **Driver:** 512.13 (Date: 3-16-2022).
- **RHI Initialization:** `D3D12` with Max Feature Level `SM5` selected and initialized successfully.
- **D3D12 Warnings/Errors:** No device removed (`DXGI_ERROR_DEVICE_REMOVED`), no memory allocation errors in log.

### 3.3 Derived Data Cache (DDC) Status (Suspect B)
- **Local DDC Server:** `zenserver.exe` (ZenServer HTTP service on `http://[::1]:8558/`) active and connected (`status: OK!`, PID 18256).
- **DDC Size:** `C:\Users\xdrhh\AppData\Local\UnrealEngine\Common\DerivedDataCache` is ~960 KB; `Intermediate/` is ~24 MB.
- **Status:** ZenServer handles the DDC cache locally. No DDC corruption error messages in log.

### 3.4 Historical Context & Previous Fix Analysis
- At 12:51 today, `太微仙宫_UE5慢速AI重构样张.png` successfully exported via SceneCapture2D (mean pixel intensity 136, max 228) using basic material `M_TaiWei_Base`.
- Inspection of `Saved/DiagShots/fix3_log.json` revealed that the previous material rebuild script (`_fix3_rebuild_materials.py`) aborted on every material because `MaterialExpressionConstant` was queried with invalid property `'value'` instead of `'r'`, causing **0 meshes** to receive valid test materials.
- Therefore, the claim that "newly created constant-color materials also render black" was potentially tainted by the script exception. A rigorous, self-contained control experiment is required.

---

## 4. Experimental Run Details
*Logs of individual diagnostic script runs.*

---

## 5. Root Cause & Definitive Fix Plan
*To be filled once definitively proved.*
