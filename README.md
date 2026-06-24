# Condor 3 `.fpl` format specification

Unofficial, reverse-engineered community documentation for the **Condor 3** flight plan (`.fpl`) file format.

## Contents

| Path | Description |
|------|-------------|
| [`FPL-format-spec.md`](FPL-format-spec.md) | Main specification (sections, keys, semantics, samples index) |
| [`spec-validation/validate_fpl.py`](spec-validation/validate_fpl.py) | Validator against the spec key inventory |
| [`spec-validation/samples/`](spec-validation/samples/) | Annotated `.fpl` samples (install, race, local, condor.club) |
| [`docs/xcsoar-ref/`](docs/xcsoar-ref/) | XCSoar Condor device driver excerpts (task import is via CoTaCo, not native `.fpl`) |

Related XCSoar discussion: [per-turnpoint altitude limits (Condor / CoTaCo import gap)](https://github.com/XCSoar/XCSoar/issues/2658).

## Status

- **Scope:** Condor 3 only (`Condor version=3000` / `3100`)
- **Not** published or endorsed by Condor Soaring Ltd.
- Last spec update: 2026-06-24 (32 C3 samples validated)

## Validation

```bash
python spec-validation/validate_fpl.py spec-validation/samples --c3-only
```

## References

- [Condor 3 User Guide](https://downloads3.condorsoaring.com/manuals/Condor%203%20manual_en.pdf)
- [CondorUTill / CoTaCo](https://condorutill.fr/)
- [FPLCheck](http://condorutill.fr/FPLCheck/FPLCheck_README.txt)
- [pycondor](https://github.com/s-celles/pycondor)

## License

Documentation and sample files: consider CC BY 4.0 unless contributors specify otherwise. XCSoar reference excerpts remain under their original GPL-2.0-or-later license.
