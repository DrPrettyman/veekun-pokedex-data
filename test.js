import {
  getPokeSpeciesByName,
  getPokeSpecies,
  getPokeSpeciesByIdentifier,
  getAllPokeSpecies,
  TOTAL_POKE_SPECIES
} from "./pokedata3g/dist/index.js";

const species = getPokeSpeciesByName("Castform");
if (!species) {
  console.log("Not found. Try a name like: Bulbasaur, Pikachu, Deoxys");
  process.exit(1);
}
console.log("\n———————————————————————————————————————————");
console.log(`#${species.id} ${species.name} — ${species.genus} Pokémon`);
console.log(species.flavorText);
console.log();
console.log("Types:", species.getTypes(3));
console.log("Stats:", species.getStats());
console.log("Egg groups:", species.eggGroups);
console.log("Abilities:", species.getAbilities());
console.log("Level moves:", species.getLevelMoves(1));
console.log("Level moves:", species.getTeachMoves(2));
console.log("Sprite:", species.getSprite("front"));
console.log("Shiny:", species.getSprite("front_shiny"));
console.log("———————————————————————————————————————————\n");

if (species.hasMultipleForms) {
  console.log("\nForms:", species.formIndices);
  for (const fi of species.formIndices) {
    const ident = species.getIdentifier(fi);
    const name = species.getFormName(fi);
    console.log(`  ${fi}: ${ident}${name ? ` (${name})` : ""}`);
    console.log(`      stats=${species.getStats(fi)} front=${species.getSprite("front", fi)}`);
  }
}
