# Proctoring Exempt Full Package

This folder contains end-to-end sample data packages for validating the `#无需编排` preset feature.

Included packages:
- `single-subjects.xlsx`
- `single-teachers.xlsx`
- `single-preset.xlsx`
- `double-subjects.xlsx`
- `double-teachers.xlsx`
- `double-preset.xlsx`

Recommended import order:
1. Import `*-subjects.xlsx` in the Subjects page.
2. Open the Proctoring page and import `*-teachers.xlsx`.
3. Import `*-preset.xlsx` through the preset import entry.
4. Run scheduling completion to fill only the remaining non-exempt slots.

Scenario highlights:
- `single-*`
  - Room 1 is marked `#无需编排`.
  - Room 2 has a preset teacher.
  - Room 3 is left blank for completion.
- `double-*`
  - Room 1 exempts slot 1 and presets slot 2.
  - Room 2 presets slot 1 and exempts slot 2.
  - Room 3 exempts both slots.
  - Room 4 is left blank for completion.
