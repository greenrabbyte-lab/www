// Compteur de la page : additionne le poids des fichiers chargés (corps compressés, mesurés par le
// navigateur) et estime l'énergie avec le modèle Sustainable Web Design v4 :
// 0,300 kWh par Go transféré (0,194 d'usage + 0,106 de fabrication, centres de données, réseaux et terminaux).
// https://sustainablewebdesign.org/estimating-digital-emissions/
(function () {
  var KWH_PAR_GO = 0.300;
  var langue = (document.documentElement.lang || "fr").slice(0, 2);
  var LOCALE = { fr: "fr-FR", en: "en-US", de: "de-DE" }[langue] || "fr-FR";
  var UNITE = langue === "fr" ? "ko" : "kB";

  function mesurer() {
    if (!window.performance || !performance.getEntriesByType) return;
    var entrees = performance.getEntriesByType("navigation").concat(performance.getEntriesByType("resource"));
    var octets = 0;
    entrees.forEach(function (e) { octets += e.encodedBodySize || e.transferSize || 0; });
    if (!octets) return;

    var poids = document.getElementById("poids");
    var energie = document.getElementById("energie");
    var wh = octets / 1e9 * KWH_PAR_GO * 1000;

    if (poids) poids.textContent = (octets / 1000).toLocaleString(LOCALE, { maximumFractionDigits: 1 }) + "\u00a0" + UNITE;
    if (energie) energie.textContent = "≈ " + wh.toLocaleString(LOCALE, { maximumSignificantDigits: 2 }) + " Wh";
  }

  if (document.readyState === "complete") setTimeout(mesurer, 0);
  else window.addEventListener("load", function () { setTimeout(mesurer, 0); });
})();
