// Compteur de la page : additionne le poids des fichiers chargés (corps compressés, mesurés par le
// navigateur) et estime l'énergie avec le modèle Sustainable Web Design v4 :
// 0,300 kWh par Go transféré (0,194 d'usage + 0,106 de fabrication, centres de données, réseaux et terminaux).
// https://sustainablewebdesign.org/estimating-digital-emissions/
(function () {
  var KWH_PAR_GO = 0.300;

  function mesurer() {
    if (!window.performance || !performance.getEntriesByType) return;
    var entrees = performance.getEntriesByType("navigation").concat(performance.getEntriesByType("resource"));
    var octets = 0;
    entrees.forEach(function (e) { octets += e.encodedBodySize || e.transferSize || 0; });
    if (!octets) return;

    var poids = document.getElementById("poids");
    var energie = document.getElementById("energie");
    var fichiers = document.getElementById("fichiers");
    var wh = octets / 1e9 * KWH_PAR_GO * 1000;

    if (poids) poids.textContent = (octets / 1000).toLocaleString("fr-FR", { maximumFractionDigits: 1 }) + " ko";
    if (energie) energie.textContent = "≈ " + wh.toLocaleString("fr-FR", { maximumSignificantDigits: 2 }) + " Wh";
    if (fichiers) fichiers.textContent = entrees.length + (entrees.length > 1 ? " fichiers" : " fichier");
  }

  if (document.readyState === "complete") setTimeout(mesurer, 0);
  else window.addEventListener("load", function () { setTimeout(mesurer, 0); });
})();
