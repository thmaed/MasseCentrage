# Masse & Centrage — données des aéroclubs

Fiches d'avions lues par l'app **Masse & Centrage** (iPhone / iPad). Un dossier par aéroclub, un fichier JSON par avion.

```
Aca/
  club.json          nom de l'aéroclub (affiché dans l'app) et « order » : ordre d'affichage des avions (immatriculations)
  F-GUVU.json        une fiche par avion, nommée d'après l'immatriculation
  …
tools/validate.py    contrôle des fiches (lancé automatiquement à chaque modification)
```

## Comment l'app se synchronise

1. Au premier usage, elle liste les dossiers qui contiennent un `club.json` et demande lequel suivre.
2. « Synchroniser » compare les fiches du dossier choisi avec celles de l'iPhone et **affiche chaque changement, avant / après**.
3. Rien n'est appliqué sans validation. Les valeurs du dépôt remplacent celles de l'iPhone pour les avions modifiés ici ; les avions ajoutés seulement sur l'iPhone sont conservés.

## Modifier une fiche

- Modifier le fichier sur GitHub (icône crayon) puis valider : l'app proposera le changement à la prochaine synchronisation.
- **`id` = immatriculation = nom du fichier** et ne change jamais (sinon l'app croit à un nouvel avion).
- Ajouter un avion : nouveau fichier `<IMMATRICULATION>.json` (copier une fiche existante de même type).
- Retirer un avion : supprimer son fichier.
- Un contrôle (GitHub Actions) refuse une fiche invalide : pesée, enveloppe, réservoirs, tableaux de performances.
- Conseil : passer par une *pull request* relue par une deuxième personne, car ces valeurs servent au calcul de masse et de centrage.

## Ajouter un aéroclub

Créer un dossier (par ex. `MonClub/`) avec un `club.json` `{ "name": "Mon aéroclub" }` et ses fiches. Il apparaîtra dans le choix de l'app.

## Avertissement

Les fiches sont une aide au calcul : elles ne remplacent ni le manuel de vol ni la fiche de pesée officielle de l'avion. Vérifier toute valeur avant le vol.
