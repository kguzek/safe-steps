# HackYeah 2025 by SolvroGen

Projekt Safe Steps w kategorii Travel.

## Live demo

<https://safe-steps.b.solvro.pl>

<img width="911" height="581" alt="image" src="https://github.com/user-attachments/assets/6cd71f06-be11-4f66-835a-ecb874bdee3a" />

## Zespół

- [Konrad Guzek](https://github.com/kguzek)
- [Paweł Pilarek](https://github.com/PilarToZiomal)
- [Marcel Musiałek](https://github.com/Marcelele-0)
- [Julia Farganus](https://github.com/farqlia)
- [Anna Poberezhna](https://github.com/AnnPoberezhna)
- [Adam Korwin](https://github.com/fidok15)

## Jak uruchomić

### Frontend

Aplikacja webowa napisana w Next.js, z package managerem pnpm.
Należy zainstalować Node.js i/lub pnpm'a, można m.in. uzyć `corepack enable`, który sam instaluje wymagany manadżer pakietów. Następnie:

```bash
pnpm i
pnpm db:generate
pnpm build
```

A do uruchomienia strony:

```bash
pnpm start
```

Next.js domyślnie uruchamia serwer HTTP na porcie 3000. Można odwiedzić: <https://localhost:3000>
