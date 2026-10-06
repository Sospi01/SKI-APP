// Station names as people say them, where OpenStreetMap's (kept in
// stations.js and the data files, which the weekly refresh rewrites) are long,
// unaccented or official-sounding: "Estació d'Esquí Baqueira-Beret" -> "Baqueira
// Beret", "Candanchu" -> "Candanchú". id -> name. Every other name is cleaned
// by rule (displayName() in index.html, display_name() in build_seo_pages.py).
// Only the shown name changes: slugs and search keep working with the old one.
var STATION_NAMES = {
  "125d02338620dc079d5d635595a099370161bf83": "Baqueira Beret",
  "de4f884c40976fe9d18c23d0bab174c1d6b79218": "Grandvalira",
  "1b306639a276ae1103bb8f7f682db30d717d65be": "Cerler",
  "5ecb06388006e4740e7ce8234e26d036ce85edb7": "Pal Arinsal",
  "7e2b2e2ae39a8764945229ed9d6314ee6d0aae47": "Astún",
  "304d72fa57c50cd759b4ebeff3e48dbee4789b17": "Candanchú",
  "066c4b2d821452980329ab1a2fd4aee2d6251231": "Ordino Arcalís",
  "d10f2f21ec726d6ca8de5886b078f40426870c4b": "San Isidro (Cebolledo y Requejines)",
  "9e00e72809ffc15563763518cdab85c73f9eccfa": "San Isidro (Saliencias)",
  "b0280114b1356e634938b8466c1f479bade260d5": "San Isidro (Riopinos)",
  "37f2df47c64be8ab0767bc65b3118e204e76e88b": "Santa Inés",
  "6ff3d800655f463f2ea8d24980630b01000c8c49": "Levi",
  "9ebf3503311da1c2e8d04a89c04e678a0d347367": "Ruka",
  // Two catalogue entries that would otherwise show the same name.
  "8ea4e409e0bbc58d0ffb58437efc4621248e9b09": "Domaine Skiable Chamrousse",
  "bc021726b4d576c20e3d1b1b55d15175eb5323a4": "Ski Center Kopaonik",
  "3b80ccceffc9f4a1723bca0c6d1610ee3d5d9bb6": "Ylläs (Ylläsjärvi)",
  "9c8c1c1000130abb373b7e6f4d7259b897b6807c": "Kotelnica Białczańska Ski Station",
  "aa317f18ea2b807c630080be922423dda830621d": "Ylläs (Äkäslompolo)",
  "b276a7bffce232c5837d4bf6e71a016afd24c5ab": "Kolašin 1600 Ski Resort"
};
