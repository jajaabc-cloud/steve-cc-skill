# Instrument Workflows

## 1. Selection And Model Suitability

Extract known conditions first:

| Item | Required Checks |
|---|---|
| Service | tag, measurement point, medium, phase, corrosive/dirty/two-phase risk |
| Process | min/normal/max flow, pressure, temperature, density, viscosity, conductivity |
| Pipe/install | DN/NPS, schedule/ID if needed, material, connection, orientation, straight run, vibration |
| Instrument | principle, range, turndown, pressure rating, temperature range, wetted material, output, power, communication |
| Compliance | Ex, SIL, material certificate, calibration certificate, local regulation, customer specification |

Then judge by instrument type:

- Pressure transmitter: range, URL/LRL, turndown, overload, static pressure, diaphragm/fill fluid, process connection, wetted material, Ex/output/power.
- Temperature sensor/thermocouple: element type, thermocouple type or RTD class, sheath/protection tube material, insertion length, response time, temperature limit, connection head, transmitter, calibration requirement.
- Temperature transmitter: sensor input type, range, cold-junction compensation, RTD wiring, accuracy, isolation, output, HART/fieldbus, Ex.
- Electromagnetic flowmeter: conductive liquid only, conductivity threshold from datasheet, liner/electrode compatibility, velocity, grounding, empty pipe, pressure/temperature limits.
- Vortex flowmeter: fluid state, velocity range, Reynolds number if data allows, density, vibration, straight run, pressure loss, steam dryness/compensation.
- Coriolis flowmeter: mass flow range, density/viscosity, gas or entrained gas risk, pressure drop, pressure/temperature rating, material, zero stability, installation stress.
- Differential-pressure flowmeter: primary element type, beta ratio or equivalent, Reynolds number, differential pressure, permanent pressure loss, straight run, tapping, pipe ID, density/viscosity/expansibility.

Conclusion must state whether the model satisfies process condition, range, pressure rating, temperature, material, connection, accuracy, installation, output/power/communication, Ex/certification, and maintenance risk.

## 2. Calculations

Show the following every time:

```text
公式：
已知条件：
单位换算：
代入：
计算结果：
工程判断：
```

Common conversions:

- Pressure: `1 MPa = 10 bar = 1000 kPa = 1,000,000 Pa`.
- Flow: distinguish `Nm3/h`, actual `m3/h`, `kg/h`, `kg/s`, `L/min`.
- Temperature: `K = degC + 273.15`.
- Velocity: `v = Q / A`; use actual volumetric flow and actual pipe ID.
- Mass/volume: `qm = rho * Qv`; ensure `Qv` is actual condition volume flow.
- Reynolds number: `Re = rho * v * D / mu`; use SI units.
- Turndown: `max flow / min flow`, or configured span versus measured range as applicable.
- Error: keep clear whether error is percent of reading, percent of span, absolute error, or standard allowed error.

If density, viscosity, pipe ID, standard condition definition, absolute pressure, or operating temperature is missing, do not force a precise flow/velocity/Reynolds conclusion.

## 3. Standard And Regulation Conformity

For standard judgments, report:

| Field | Requirement |
|---|---|
| Standard | name, number, year/version |
| Scope | why the standard applies to this instrument/task |
| Clause/page | clause or page basis from source document |
| Allowance | allowed error/tolerance/requirement |
| Evidence | measured data, datasheet parameter, calculation result |
| Conclusion | compliant / non-compliant / conditionally compliant / cannot judge |
| Risk | boundary points, missing data, calibration condition mismatch |

Do not quote a clause number unless it was found in the source document. If only a scanned page image is available, visually verify the page before citing it.

## 4. Calibration And Accuracy Data

For calibration tables or error curves:

1. Identify reference standard, DUT, range, points, units, ambient conditions, and traceability if provided.
2. Convert units before error calculation.
3. Calculate error at each point and compare with the applicable tolerance.
4. Distinguish ascending/descending runs, repeatability, hysteresis, indication error, and uncertainty if present.
5. Plot curves only from provided data. Label axes with units and preserve raw data in the workbook or output directory.
6. State pass/fail per point and overall. If acceptance criteria are missing, say they are missing and explain the effect.

## 5. Formal Output Structure

Use this structure for reports unless the user requests a different format:

1. 项目概述
2. 已知条件
3. 采用资料和标准
4. 计算过程
5. 选型或符合性分析
6. 风险与需确认项
7. 结论
8. 附录

Use tables for known conditions, source basis, model comparison, risk items, and missing parameters. Keep the language formal and suitable for customer or internal engineering review.
