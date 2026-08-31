import React, { useEffect, useMemo, useState } from "react";

var API_URL = "http://127.0.0.1:5000";
var PAGE_SIZE = 25;
var STORAGE_KEY_ROSA = "fantacalcio_rosa_2026";
var STORAGE_KEY_BUDGET = "fantacalcio_budget_2026";
var STORAGE_KEY_LEGA = "fantacalcio_lega_2026";
var DEFAULT_BUDGET = 500;

var DEFAULT_VINCOLI = {
    P: 3,
    D: 8,
    C: 8,
    A: 6,
    TOTALE: 25
};

var SECTIONS = [
    { id: "asta", label: "Asta" },
    { id: "rosa", label: "La mia rosa" },
    { id: "lega", label: "La mia lega" },
    { id: "formazione", label: "Formazione" },
    { id: "mercato", label: "Mercato" },
    { id: "regolamento", label: "Lega CertiFanta" }
];

var MODULI = [
    { id: "3-4-3", D: 3, C: 4, A: 3 },
    { id: "3-5-2", D: 3, C: 5, A: 2 },
    { id: "4-3-3", D: 4, C: 3, A: 3 },
    { id: "4-4-2", D: 4, C: 4, A: 2 },
    { id: "4-5-1", D: 4, C: 5, A: 1 },
    { id: "5-3-2", D: 5, C: 3, A: 2 },
    { id: "5-4-1", D: 5, C: 4, A: 1 }
];

var MODULI_NON_AMMESSI = ["3-3-4", "4-2-4", "3-6-1"];

function formatNumber(value, decimals) {
    if (decimals === undefined) decimals = 2;
    return Number(value || 0).toFixed(decimals);
}

function getRoleColor(role) {
    if (role === "P") return "#2563eb";
    if (role === "D") return "#16a34a";
    if (role === "C") return "#ca8a04";
    if (role === "A") return "#dc2626";
    return "#64748b";
}

function getVincoliLega() {
    try {
        var saved = JSON.parse(
            localStorage.getItem(STORAGE_KEY_LEGA) || "null"
        );
        if (!saved) return DEFAULT_VINCOLI;
        return mergeObjects(DEFAULT_VINCOLI, saved);
    } catch (e) {
        return DEFAULT_VINCOLI;
    }
}

function mergeObjects(base, extra) {
    var result = {};
    var key;
    for (key in base) {
        if (base.hasOwnProperty(key)) {
            result[key] = base[key];
        }
    }
    for (key in extra) {
        if (extra.hasOwnProperty(key)) {
            result[key] = extra[key];
        }
    }
    return result;
}

function saveVincoliLega(vincoli) {
    localStorage.setItem(
        STORAGE_KEY_LEGA,
        JSON.stringify(vincoli)
    );
}

function getNomeLega() {
    try {
        return localStorage.getItem("fantacalcio_nome_lega") || "La mia lega";
    } catch (e) {
        return "La mia lega";
    }
}

function saveNomeLega(nome) {
    localStorage.setItem("fantacalcio_nome_lega", nome);
}

function exportRosaToCsv(rosa) {
    var header = [
        "player_id",
        "name",
        "role",
        "team",
        "price",
        "fantamedia",
        "presenze",
        "gol_fatti",
        "assist"
    ];

    var rows = rosa.map(function (p) {
        var nameSafe = String(p.name || "").replace(/"/g, '""');
        var teamSafe = String(p.team || "").replace(/"/g, '""');

        return [
            p.player_id,
            '"' + nameSafe + '"',
            p.role,
            '"' + teamSafe + '"',
            p.price,
            p.fantamedia,
            p.presenze,
            p.gol_fatti,
            p.assist
        ].join(",");
    });

    var csvLines = [];
    csvLines.push(header.join(","));

    var i = 0;
    while (i < rows.length) {
        csvLines.push(rows[i]);
        i = i + 1;
    }

    var newline = String.fromCharCode(10);
    var csvContent = csvLines.join(newline);

    var blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);

    var link = document.createElement("a");
    link.href = url;
    link.download = "mia_rosa_fantacalcio.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
}

function App() {
    var activeSection = useState("asta")[0];
    var setActiveSection = useState("asta")[1];

    var players = useState([])[0];
    var setPlayers = useState([])[1];
    var loading = useState(true)[0];
    var setLoading = useState(true)[1];
    var errorMessage = useState("")[0];
    var setErrorMessage = useState("")[1];

    var searchText = useState("")[0];
    var setSearchText = useState("")[1];
    var selectedRole = useState("Tutti")[0];
    var setSelectedRole = useState("Tutti")[1];
    var selectedTeam = useState("Tutte")[0];
    var setSelectedTeam = useState("Tutte")[1];
    var currentPage = useState(1)[0];
    var setCurrentPage = useState(1)[1];

    var rosa = useState([])[0];
    var setRosa = useState([])[1];
    var budget = useState(DEFAULT_BUDGET)[0];
    var setBudget = useState(DEFAULT_BUDGET)[1];

    var moduloScelto = useState("3-4-3")[0];
    var setModuloScelto = useState("3-4-3")[1];

    var nomeLega = useState(getNomeLega())[0];
    var setNomeLega = useState(getNomeLega())[1];
    var vincoliLega = useState(getVincoliLega())[0];
    var setVincoliLega = useState(getVincoliLega())[1];

    var nomeLegaInput = useState(nomeLega)[0];
    var setNomeLegaInput = useState(nomeLega)[1];
    var vincoliInput = useState(mergeObjects({}, vincoliLega))[0];
    var setVincoliInput = useState(mergeObjects({}, vincoliLega))[1];

    useEffect(function () {
        async function loadPlayers() {
            try {
                setLoading(true);
                setErrorMessage("");

                var response = await fetch(API_URL + "/api/auction");

                if (!response.ok) {
                    throw new Error("Backend non raggiungibile");
                }

                var data = await response.json();

                setPlayers(data.items || []);
            } catch (error) {
                setErrorMessage(
                    "Impossibile caricare i giocatori. Controlla che Flask sia attivo."
                );
            } finally {
                setLoading(false);
            }
        }

        loadPlayers();
    }, []);

    useEffect(function () {
        try {
            var savedRosa = JSON.parse(
                localStorage.getItem(STORAGE_KEY_ROSA) || "[]"
            );

            var savedBudget = Number(
                localStorage.getItem(STORAGE_KEY_BUDGET) || DEFAULT_BUDGET
            );

            setRosa(savedRosa);
            setBudget(savedBudget || DEFAULT_BUDGET);
        } catch (e) {
            setRosa([]);
            setBudget(DEFAULT_BUDGET);
        }
    }, []);

    function saveRosa(newRosa) {
        setRosa(newRosa);
        localStorage.setItem(STORAGE_KEY_ROSA, JSON.stringify(newRosa));
    }

    function saveBudget(newBudget) {
        setBudget(newBudget);
        localStorage.setItem(STORAGE_KEY_BUDGET, String(newBudget));
    }

    function aggiungiAllaRosa(player) {
        var giaInRosa = rosa.find(
            function (p) { return p.player_id === player.player_id; }
        );

        if (giaInRosa) {
            alert("Questo giocatore è già nella tua rosa.");
            return;
        }

        var ruolo = String(player.role || "");
        var conteggioRuolo = rosa.filter(
            function (p) { return p.role === ruolo; }
        ).length;

        if (conteggioRuolo >= vincoliLega[ruolo]) {
            alert(
                "Hai già raggiunto il massimo di " + vincoliLega[ruolo] + " giocatori per il ruolo " + ruolo + "."
            );
            return;
        }

        if (rosa.length >= vincoliLega.TOTALE) {
            alert(
                "Hai già raggiunto il massimo di " + vincoliLega.TOTALE + " giocatori in rosa."
            );
            return;
        }

        var prezzo = Number(prompt(
            "Prezzo di acquisto per " + player.name + "?",
            String(player.price || 1)
        ));

        if (prezzo === null || isNaN(prezzo)) {
            return;
        }

        var nuovoGiocatore = {
            player_id: player.player_id,
            name: player.name,
            role: player.role,
            team: player.team,
            price: Number(prezzo),
            fantamedia: player.fantamedia,
            presenze: player.presenze,
            gol_fatti: player.gol_fatti,
            assist: player.assist
        };

        var nuovaRosa = rosa.concat([nuovoGiocatore]);
        saveRosa(nuovaRosa);

        alert(player.name + " aggiunto alla rosa a " + prezzo + " crediti.");
    }

    function rimuoviDallaRosa(playerId) {
        var giocatore = rosa.find(function (p) { return p.player_id === playerId; });

        if (!giocatore) return;

        var ok = confirm(
            "Rimuovere " + giocatore.name + " dalla rosa?"
        );

        if (!ok) return;

        var nuovaRosa = rosa.filter(
            function (p) { return p.player_id !== playerId; }
        );

        saveRosa(nuovaRosa);
    }

    var teams = useMemo(function () {
        var availableTeams = players
            .map(function (player) { return player.team; })
            .filter(Boolean);

        return ["Tutte"].concat(
            Array.from(new Set(availableTeams)).sort()
        );
    }, [players]);

    var filteredPlayers = useMemo(function () {
        var cleanSearch = searchText.trim().toLowerCase();

        return players.filter(function (player) {
            var name = String(player.name || "").toLowerCase();

            var searchMatches =
                cleanSearch === "" ||
                name.indexOf(cleanSearch) !== -1;

            var roleMatches =
                selectedRole === "Tutti" ||
                player.role === selectedRole;

            var teamMatches =
                selectedTeam === "Tutte" ||
                player.team === selectedTeam;

            return searchMatches && roleMatches && teamMatches;
        });
    }, [players, searchText, selectedRole, selectedTeam]);

    var totalPages = Math.max(
        1,
        Math.ceil(filteredPlayers.length / PAGE_SIZE)
    );

    var visiblePlayers = useMemo(function () {
        var page = Math.min(currentPage, totalPages);
        var startIndex = (page - 1) * PAGE_SIZE;

        return filteredPlayers.slice(
            startIndex,
            startIndex + PAGE_SIZE
        );
    }, [filteredPlayers, currentPage, totalPages]);

    useEffect(function () {
        setCurrentPage(1);
    }, [searchText, selectedRole, selectedTeam]);

    var spesaTotale = useMemo(
        function () {
            return rosa.reduce(function (sum, p) {
                return sum + (Number(p.price) || 0);
            }, 0);
        },
        [rosa]
    );

    var budgetResiduo = budget - spesaTotale;

    var rosaPerRuolo = useMemo(function () {
        var conteggio = { P: 0, D: 0, C: 0, A: 0 };

        rosa.forEach(function (p) {
            var role = String(p.role || "");
            if (conteggio.hasOwnProperty(role)) {
                conteggio[role] += 1;
            }
        });

        return conteggio;
    }, [rosa]);

    var rosaPerRuoloOrdinata = useMemo(function () {
        var perRuolo = {
            P: [],
            D: [],
            C: [],
            A: []
        };

        rosa.forEach(function (p) {
            var role = String(p.role || "");
            if (perRuolo.hasOwnProperty(role)) {
                perRuolo[role].push(p);
            }
        });

        ["P", "D", "C", "A"].forEach(function (role) {
            perRuolo[role].sort(
                function (a, b) {
                    return Number(b.fantamedia || 0) - Number(a.fantamedia || 0);
                }
            );
        });

        return perRuolo;
    }, [rosa]);

    var moduloCorrente = useMemo(
        function () {
            var found = MODULI.find(function (m) { return m.id === moduloScelto; });
            return found || MODULI[0];
        },
        [moduloScelto]
    );

    var formazioneCalcolata = useMemo(function () {
        var portieri = rosaPerRuoloOrdinata.P;
        var difensori = rosaPerRuoloOrdinata.D;
        var centrocampisti = rosaPerRuoloOrdinata.C;
        var attaccanti = rosaPerRuoloOrdinata.A;

        var titolareP = portieri[0] || null;

        var titolariD = difensori.slice(0, moduloCorrente.D);
        var titolariC = centrocampisti.slice(0, moduloCorrente.C);
        var titolariA = attaccanti.slice(0, moduloCorrente.A);

        var panchinaD = difensori.slice(moduloCorrente.D);
        var panchinaC = centrocampisti.slice(moduloCorrente.C);
        var panchinaA = attaccanti.slice(moduloCorrente.A);
        var panchinaP = portieri.slice(1);

        var titolari = [
            titolareP
        ].concat(titolariD, titolariC, titolariA).filter(Boolean);

        var panchina = [].concat(panchinaP, panchinaD, panchinaC, panchinaA);

        var punteggioMedioTitolari = titolari.reduce(
            function (sum, p) { return sum + (Number(p.fantamedia) || 0); },
            0
        );

        return {
            modulo: moduloCorrente.id,
            portiere: titolareP,
            difensori: titolariD,
            centrocampisti: titolariC,
            attaccanti: titolariA,
            panchina: panchina,
            punteggioMedioTitolari: punteggioMedioTitolari
        };
    }, [rosaPerRuoloOrdinata, moduloCorrente]);

    function renderAsta() {
        return React.createElement(React.Fragment, null,
            React.createElement("section", { style: styles.filters },
                React.createElement("input", {
                    style: styles.input,
                    type: "text",
                    value: searchText,
                    onChange: function (event) { setSearchText(event.target.value); },
                    placeholder: "Cerca giocatore"
                }),
                React.createElement("select", {
                    style: styles.select,
                    value: selectedRole,
                    onChange: function (event) { setSelectedRole(event.target.value); }
                },
                    React.createElement("option", { value: "Tutti" }, "Tutti i ruoli"),
                    React.createElement("option", { value: "P" }, "P - Portieri"),
                    React.createElement("option", { value: "D" }, "D - Difensori"),
                    React.createElement("option", { value: "C" }, "C - Centrocampisti"),
                    React.createElement("option", { value: "A" }, "A - Attaccanti")
                ),
                React.createElement("select", {
                    style: styles.select,
                    value: selectedTeam,
                    onChange: function (event) { setSelectedTeam(event.target.value); }
                },
                    teams.map(function (team) {
                        return React.createElement("option", { key: team, value: team },
                            team === "Tutte" ? "Tutte le squadre" : team
                        );
                    })
                )
            ),
            React.createElement("p", { style: styles.results },
                "Giocatori trovati: ",
                React.createElement("strong", null, filteredPlayers.length),
                " • Pagina ",
                Math.min(currentPage, totalPages),
                " di ",
                totalPages
            ),
            React.createElement("section", { style: styles.tableContainer },
                React.createElement("table", { style: styles.table },
                    React.createElement("thead", null,
                        React.createElement("tr", null,
                            React.createElement("th", { style: styles.tableHeader }, "Giocatore"),
                            React.createElement("th", { style: styles.tableHeader }, "Ruolo"),
                            React.createElement("th", { style: styles.tableHeader }, "Squadra"),
                            React.createElement("th", { style: styles.tableHeader }, "Valore"),
                            React.createElement("th", { style: styles.tableHeader }, "FantaM."),
                            React.createElement("th", { style: styles.tableHeader }, "Pres."),
                            React.createElement("th", { style: styles.tableHeader }, "Gol"),
                            React.createElement("th", { style: styles.tableHeader }, "Assist"),
                            React.createElement("th", { style: styles.tableHeader }, "Bonus"),
                            React.createElement("th", { style: styles.tableHeader }, "Malus"),
                            React.createElement("th", { style: styles.tableHeader }, "Azione")
                        )
                    ),
                    React.createElement("tbody", null,
                        visiblePlayers.map(function (player) {
                            return React.createElement("tr", { key: player.player_id },
                                React.createElement("td", { style: styles.playerName }, player.name),
                                React.createElement("td", { style: styles.tableCell },
                                    React.createElement("span", {
                                        style: mergeObjects({}, styles.roleBadge, {
                                            backgroundColor: getRoleColor(player.role)
                                        })
                                    }, player.role)
                                ),
                                React.createElement("td", { style: styles.tableCell }, player.team),
                                React.createElement("td", { style: styles.tableCell }, formatNumber(player.price, 1)),
                                React.createElement("td", { style: styles.tableCell }, formatNumber(player.fantamedia)),
                                React.createElement("td", { style: styles.tableCell }, player.presenze),
                                React.createElement("td", { style: styles.tableCell }, player.gol_fatti),
                                React.createElement("td", { style: styles.tableCell }, player.assist),
                                React.createElement("td", { style: styles.tableCell }, formatNumber(player.expected_bonus)),
                                React.createElement("td", { style: styles.tableCell }, formatNumber(player.expected_malus)),
                                React.createElement("td", { style: styles.tableCell },
                                    React.createElement("button", {
                                        style: styles.addButton,
                                        onClick: function () { aggiungiAllaRosa(player); }
                                    }, "+ Rosa")
                                )
                            );
                        })
                    )
                ),
                visiblePlayers.length === 0 &&
                React.createElement("div", { style: styles.empty }, "Nessun giocatore trovato con questi filtri.")
            ),
            React.createElement("section", { style: styles.pagination },
                React.createElement("button", {
                    style: styles.button,
                    disabled: currentPage <= 1,
                    onClick: function () { setCurrentPage(currentPage - 1); }
                }, "← Precedente"),
                React.createElement("span", null,
                    "Pagina ", Math.min(currentPage, totalPages), " / ", totalPages
                ),
                React.createElement("button", {
                    style: styles.button,
                    disabled: currentPage >= totalPages,
                    onClick: function () { setCurrentPage(currentPage + 1); }
                }, "Successiva →")
            )
        );
    }

    function renderRosa() {
        var rosaPiena = rosa.length >= vincoliLega.TOTALE;

        return React.createElement(React.Fragment, null,
            React.createElement("section", { style: styles.card },
                React.createElement("h2", { style: styles.sectionTitle }, "La mia rosa"),
                React.createElement("div", { style: styles.exportRow },
                    React.createElement("button", {
                        style: styles.exportButton,
                        onClick: function () {
                            if (rosa.length === 0) {
                                alert("La tua rosa è vuota.");
                                return;
                            }
                            exportRosaToCsv(rosa);
                        }
                    }, "Esporta CSV rosa")
                ),
                React.createElement("div", { style: styles.budgetRow },
                    React.createElement("div", { style: styles.budgetInput },
                        React.createElement("label", { style: styles.budgetLabel }, "Budget iniziale (crediti)"),
                        React.createElement("input", {
                            style: styles.budgetField,
                            type: "number",
                            value: budget,
                            onChange: function (event) {
                                var nuovo = Number(event.target.value);
                                if (!isNaN(nuovo) && nuovo >= 0) {
                                    saveBudget(nuovo);
                                }
                            }
                        })
                    ),
                    React.createElement("div", { style: styles.budgetSummary },
                        React.createElement("div", { style: styles.budgetItem },
                            React.createElement("span", null, "Spesa totale"),
                            React.createElement("strong", null, formatNumber(spesaTotale, 1))
                        ),
                        React.createElement("div", { style: styles.budgetItem },
                            React.createElement("span", null, "Budget residuo"),
                            React.createElement("strong", {
                                style: {
                                    color: budgetResiduo < 0 ? "#dc2626" : "#166534"
                                }
                            }, formatNumber(budgetResiduo, 1))
                        )
                    )
                ),
                React.createElement("div", { style: styles.rosterSummary },
                    React.createElement("div", { style: styles.rosterTotal },
                        React.createElement("span", null, "Giocatori in rosa"),
                        React.createElement("strong", null,
                            rosa.length, " / ", vincoliLega.TOTALE
                        )
                    ),
                    rosaPiena &&
                    React.createElement("div", { style: styles.rosterFull }, "Rosa completa: non puoi aggiungere altri giocatori.")
                ),
                React.createElement("div", { style: styles.roleLimitsGrid },
                    React.createElement("div", { style: styles.roleLimitCard },
                        React.createElement("span", { style: styles.roleLimitLabel }, "Portieri"),
                        React.createElement("div", { style: styles.roleLimitBar },
                            React.createElement("span", {
                                style: mergeObjects({}, styles.roleLimitValue, {
                                    color: rosaPerRuolo.P >= vincoliLega.P ? "#166534" : "#b91c1c"
                                })
                            }, rosaPerRuolo.P, " / ", vincoliLega.P)
                        )
                    ),
                    React.createElement("div", { style: styles.roleLimitCard },
                        React.createElement("span", { style: styles.roleLimitLabel }, "Difensori"),
                        React.createElement("div", { style: styles.roleLimitBar },
                            React.createElement("span", {
                                style: mergeObjects({}, styles.roleLimitValue, {
                                    color: rosaPerRuolo.D >= vincoliLega.D ? "#166534" : "#b91c1c"
                                })
                            }, rosaPerRuolo.D, " / ", vincoliLega.D)
                        )
                    ),
                    React.createElement("div", { style: styles.roleLimitCard },
                        React.createElement("span", { style: styles.roleLimitLabel }, "Centrocampisti"),
                        React.createElement("div", { style: styles.roleLimitBar },
                            React.createElement("span", {
                                style: mergeObjects({}, styles.roleLimitValue, {
                                    color: rosaPerRuolo.C >= vincoliLega.C ? "#166534" : "#b91c1c"
                                })
                            }, rosaPerRuolo.C, " / ", vincoliLega.C)
                        )
                    ),
                    React.createElement("div", { style: styles.roleLimitCard },
                        React.createElement("span", { style: styles.roleLimitLabel }, "Attaccanti"),
                        React.createElement("div", { style: styles.roleLimitBar },
                            React.createElement("span", {
                                style: mergeObjects({}, styles.roleLimitValue, {
                                    color: rosaPerRuolo.A >= vincoliLega.A ? "#166534" : "#b91c1c"
                                })
                            }, rosaPerRuolo.A, " / ", vincoliLega.A)
                        )
                    )
                ),
                React.createElement("p", { style: styles.note },
                    "La lega prevede una rosa massima di " + vincoliLega.TOTALE + " giocatori: " +
                    vincoliLega.P + " portieri, " + vincoliLega.D + " difensori, " +
                    vincoliLega.C + " centrocampisti e " + vincoliLega.A + " attaccanti."
                )
            ),
            React.createElement("section", { style: styles.tableContainer },
                React.createElement("table", { style: styles.table },
                    React.createElement("thead", null,
                        React.createElement("tr", null,
                            React.createElement("th", { style: styles.tableHeader }, "Giocatore"),
                            React.createElement("th", { style: styles.tableHeader }, "Ruolo"),
                            React.createElement("th", { style: styles.tableHeader }, "Squadra"),
                            React.createElement("th", { style: styles.tableHeader }, "Prezzo"),
                            React.createElement("th", { style: styles.tableHeader }, "FantaM."),
                            React.createElement("th", { style: styles.tableHeader }, "Pres."),
                            React.createElement("th", { style: styles.tableHeader }, "Gol"),
                            React.createElement("th", { style: styles.tableHeader }, "Assist"),
                            React.createElement("th", { style: styles.tableHeader }, "Azione")
                        )
                    ),
                    React.createElement("tbody", null,
                        rosa.map(function (player) {
                            return React.createElement("tr", { key: player.player_id },
                                React.createElement("td", { style: styles.playerName }, player.name),
                                React.createElement("td", { style: styles.tableCell },
                                    React.createElement("span", {
                                        style: mergeObjects({}, styles.roleBadge, {
                                            backgroundColor: getRoleColor(player.role)
                                        })
                                    }, player.role)
                                ),
                                React.createElement("td", { style: styles.tableCell }, player.team),
                                React.createElement("td", { style: styles.tableCell }, formatNumber(player.price, 1)),
                                React.createElement("td", { style: styles.tableCell }, formatNumber(player.fantamedia)),
                                React.createElement("td", { style: styles.tableCell }, player.presenze),
                                React.createElement("td", { style: styles.tableCell }, player.gol_fatti),
                                React.createElement("td", { style: styles.tableCell }, player.assist),
                                React.createElement("td", { style: styles.tableCell },
                                    React.createElement("button", {
                                        style: styles.removeButton,
                                        onClick: function () { rimuoviDallaRosa(player.player_id); }
                                    }, "Rimuovi")
                                )
                            );
                        })
                    )
                ),
                rosa.length === 0 &&
                React.createElement("div", { style: styles.empty }, "La tua rosa è vuota. Torna nella sezione Asta e aggiungi i primi giocatori.")
            )
        );
    }

    function renderLegaSettings() {
        return React.createElement("section", { style: styles.card },
            React.createElement("h2", { style: styles.sectionTitle }, "La mia lega"),
            React.createElement("div", { style: styles.legaSettingsGrid },
                React.createElement("div", { style: styles.legaSettingCard },
                    React.createElement("h3", { style: styles.legaSettingTitle }, "Nome della lega"),
                    React.createElement("input", {
                        style: styles.legaInput,
                        type: "text",
                        value: nomeLegaInput,
                        onChange: function (event) { setNomeLegaInput(event.target.value); },
                        placeholder: "Inserisci il nome della lega"
                    }),
                    React.createElement("button", {
                        style: styles.legaButton,
                        onClick: function () {
                            var nome = nomeLegaInput.trim() || "La mia lega";
                            setNomeLega(nome);
                            saveNomeLega(nome);
                            alert("Nome lega salvato.");
                        }
                    }, "Salva nome lega")
                ),
                React.createElement("div", { style: styles.legaSettingCard },
                    React.createElement("h3", { style: styles.legaSettingTitle }, "Vincoli della rosa"),
                    React.createElement("div", { style: styles.vincoliGrid },
                        React.createElement("div", { style: styles.vincoloRow },
                            React.createElement("label", { style: styles.vincoloLabel }, "Max portieri"),
                            React.createElement("input", {
                                style: styles.vincoloInput,
                                type: "number",
                                value: vincoliInput.P,
                                onChange: function (event) {
                                    var v = Number(event.target.value);
                                    setVincoliInput(mergeObjects({}, vincoliInput, { P: v }));
                                }
                            })
                        ),
                        React.createElement("div", { style: styles.vincoloRow },
                            React.createElement("label", { style: styles.vincoloLabel }, "Max difensori"),
                            React.createElement("input", {
                                style: styles.vincoloInput,
                                type: "number",
                                value: vincoliInput.D,
                                onChange: function (event) {
                                    var v = Number(event.target.value);
                                    setVincoliInput(mergeObjects({}, vincoliInput, { D: v }));
                                }
                            })
                        ),
                        React.createElement("div", { style: styles.vincoloRow },
                            React.createElement("label", { style: styles.vincoloLabel }, "Max centrocampisti"),
                            React.createElement("input", {
                                style: styles.vincoloInput,
                                type: "number",
                                value: vincoliInput.C,
                                onChange: function (event) {
                                    var v = Number(event.target.value);
                                    setVincoliInput(mergeObjects({}, vincoliInput, { C: v }));
                                }
                            })
                        ),
                        React.createElement("div", { style: styles.vincoloRow },
                            React.createElement("label", { style: styles.vincoloLabel }, "Max attaccanti"),
                            React.createElement("input", {
                                style: styles.vincoloInput,
                                type: "number",
                                value: vincoliInput.A,
                                onChange: function (event) {
                                    var v = Number(event.target.value);
                                    setVincoliInput(mergeObjects({}, vincoliInput, { A: v }));
                                }
                            })
                        ),
                        React.createElement("div", { style: styles.vincoloRow },
                            React.createElement("label", { style: styles.vincoloLabel }, "Totale giocatori"),
                            React.createElement("input", {
                                style: styles.vincoloInput,
                                type: "number",
                                value: vincoliInput.TOTALE,
                                onChange: function (event) {
                                    var v = Number(event.target.value);
                                    setVincoliInput(mergeObjects({}, vincoliInput, { TOTALE: v }));
                                }
                            })
                        )
                    ),
                    React.createElement("button", {
                        style: styles.legaButton,
                        onClick: function () {
                            var nuoviVincoli = {
                                P: Math.max(1, vincoliInput.P),
                                D: Math.max(1, vincoliInput.D),
                                C: Math.max(1, vincoliInput.C),
                                A: Math.max(1, vincoliInput.A),
                                TOTALE: Math.max(11, vincoliInput.TOTALE)
                            };
                            setVincoliLega(nuoviVincoli);
                            saveVincoliLega(nuoviVincoli);
                            alert("Vincoli della lega salvati.");
                        }
                    }, "Salva vincoli"),
                    React.createElement("p", { style: styles.note }, "Questi valori verranno usati per i limiti nella rosa, nel mercato e nella formazione.")
                )
            )
        );
    }

    function renderFormazione() {
        var modulo = formazioneCalcolata.modulo;
        var portiere = formazioneCalcolata.portiere;
        var difensori = formazioneCalcolata.difensori;
        var centrocampisti = formazioneCalcolata.centrocampisti;
        var attaccanti = formazioneCalcolata.attaccanti;
        var panchina = formazioneCalcolata.panchina;
        var punteggioMedioTitolari = formazioneCalcolata.punteggioMedioTitolari;

        var rosaInsufficiente =
            rosaPerRuolo.P === 0 ||
            rosaPerRuolo.D + rosaPerRuolo.C + rosaPerRuolo.A < 10;

        return React.createElement("section", { style: styles.card },
            React.createElement("h2", { style: styles.sectionTitle }, "Formazione suggerita"),
            React.createElement("div", { style: styles.moduloRow },
                React.createElement("label", { style: styles.moduloLabel }, "Modulo:"),
                React.createElement("select", {
                    style: styles.moduloSelect,
                    value: moduloScelto,
                    onChange: function (event) { setModuloScelto(event.target.value); }
                },
                    MODULI.map(function (m) {
                        return React.createElement("option", { key: m.id, value: m.id }, m.id);
                    })
                )
            ),
            rosaInsufficiente ?
                React.createElement("div", { style: styles.warningBox },
                    React.createElement("strong", null, "Rosa insufficiente"),
                    React.createElement("p", null, "Per calcolare una formazione servono almeno: 1 portiere e 10 giocatori di movimento.")
                ) :
                React.createElement(React.Fragment, null,
                    React.createElement("div", { style: styles.summaryBox },
                        React.createElement("div", { style: styles.summaryItem },
                            React.createElement("span", null, "Modulo"),
                            React.createElement("strong", null, modulo)
                        ),
                        React.createElement("div", { style: styles.summaryItem },
                            React.createElement("span", null, "Punteggio medio titolari"),
                            React.createElement("strong", null, formatNumber(punteggioMedioTitolari))
                        )
                    ),
                    React.createElement("h3", { style: styles.subTitle }, "Titolari"),
                    React.createElement("div", { style: styles.formationGrid },
                        portiere &&
                        React.createElement("div", { style: styles.playerCard },
                            React.createElement("span", { style: styles.roleBadgeSmall }, "P"),
                            React.createElement("strong", null, portiere.name),
                            React.createElement("span", null, portiere.team),
                            React.createElement("span", null, "FM: ", formatNumber(portiere.fantamedia))
                        ),
                        difensori.map(function (p) {
                            return React.createElement("div", { key: p.player_id, style: styles.playerCard },
                                React.createElement("span", { style: styles.roleBadgeSmall }, "D"),
                                React.createElement("strong", null, p.name),
                                React.createElement("span", null, p.team),
                                React.createElement("span", null, "FM: ", formatNumber(p.fantamedia))
                            );
                        }),
                        centrocampisti.map(function (p) {
                            return React.createElement("div", { key: p.player_id, style: styles.playerCard },
                                React.createElement("span", { style: styles.roleBadgeSmall }, "C"),
                                React.createElement("strong", null, p.name),
                                React.createElement("span", null, p.team),
                                React.createElement("span", null, "FM: ", formatNumber(p.fantamedia))
                            );
                        }),
                        attaccanti.map(function (p) {
                            return React.createElement("div", { key: p.player_id, style: styles.playerCard },
                                React.createElement("span", { style: styles.roleBadgeSmall }, "A"),
                                React.createElement("strong", null, p.name),
                                React.createElement("span", null, p.team),
                                React.createElement("span", null, "FM: ", formatNumber(p.fantamedia))
                            );
                        })
                    ),
                    panchina.length > 0 &&
                    React.createElement(React.Fragment, null,
                        React.createElement("h3", { style: styles.subTitle }, "Panchina"),
                        React.createElement("div", { style: styles.benchList },
                            panchina.map(function (p) {
                                return React.createElement("div", { key: p.player_id, style: styles.benchRow },
                                    React.createElement("span", {
                                        style: mergeObjects({}, styles.roleBadgeSmall, {
                                            backgroundColor: getRoleColor(p.role)
                                        })
                                    }, p.role),
                                    React.createElement("strong", null, p.name),
                                    React.createElement("span", null, p.team),
                                    React.createElement("span", null, "FM: ", formatNumber(p.fantamedia))
                                );
                            })
                        )
                    )
                )
        );
    }

    function renderMercato() {
        var postiRestanti = {
            P: vincoliLega.P - rosaPerRuolo.P,
            D: vincoliLega.D - rosaPerRuolo.D,
            C: vincoliLega.C - rosaPerRuolo.C,
            A: vincoliLega.A - rosaPerRuolo.A
        };

        var totaleRestante =
            postiRestanti.P +
            postiRestanti.D +
            postiRestanti.C +
            postiRestanti.A;

        var ruoliDaCoprire = Object.entries(postiRestanti)
            .filter(function (entry) { return entry[1] > 0; })
            .map(function (entry) {
                var role = entry[0];
                var count = entry[1];
                var label =
                    role === "P" ? "Portieri" :
                        role === "D" ? "Difensori" :
                            role === "C" ? "Centrocampisti" : "Attaccanti";
                return { role: role, count: count, label: label };
            });

        return React.createElement("section", { style: styles.card },
            React.createElement("h2", { style: styles.sectionTitle }, "Mercato"),
            React.createElement("p", { style: styles.sectionText },
                "La tua rosa può ancora accogliere ",
                React.createElement("strong", null, totaleRestante),
                " giocatori."
            ),
            ruoliDaCoprire.length === 0 ?
                React.createElement("div", { style: styles.warningBox },
                    React.createElement("strong", null, "Rosa completa per ruolo"),
                    React.createElement("p", null, "Hai già raggiunto il massimo di giocatori per ogni ruolo. Per aggiungere nuovi giocatori, devi prima rimuoverne alcuni.")
                ) :
                React.createElement(React.Fragment, null,
                    React.createElement("h3", { style: styles.subTitle }, "Ruoli da coprire"),
                    React.createElement("div", { style: styles.marketNeedsGrid },
                        ruoliDaCoprire.map(function (item) {
                            return React.createElement("div", { key: item.role, style: styles.marketNeedCard },
                                React.createElement("span", { style: styles.marketNeedLabel }, item.label),
                                React.createElement("strong", { style: styles.marketNeedValue }, item.count, " da acquistare")
                            );
                        })
                    ),
                    React.createElement("p", { style: styles.note }, "Prossimo passo: mostrare giocatori consigliati per ciascun ruolo scoperto, in base alla FantaMedia e al prezzo.")
                )
        );
    }

    function renderRegolamento() {
        return React.createElement("section", { style: styles.card },
            React.createElement("h2", { style: styles.sectionTitle }, "Lega CertiFanta"),
            React.createElement("div", { style: styles.leagueInfoGrid },
                React.createElement("div", { style: styles.leagueInfoCard },
                    React.createElement("h3", { style: styles.leagueInfoTitle }, "Composizione della rosa"),
                    React.createElement("ul", { style: styles.leagueList },
                        React.createElement("li", null, React.createElement("strong", null, "Totale giocatori:"), " ", vincoliLega.TOTALE),
                        React.createElement("li", null, React.createElement("strong", null, "Portieri:"), " ", vincoliLega.P),
                        React.createElement("li", null, React.createElement("strong", null, "Difensori:"), " ", vincoliLega.D),
                        React.createElement("li", null, React.createElement("strong", null, "Centrocampisti:"), " ", vincoliLega.C),
                        React.createElement("li", null, React.createElement("strong", null, "Attaccanti:"), " ", vincoliLega.A),
                        React.createElement("li", null, React.createElement("strong", null, "Panchina:"), " 14 giocatori")
                    ),
                    React.createElement("p", { style: styles.note }, "La lega prevede una rosa da " + vincoliLega.TOTALE + " giocatori (11 titolari + 14 di panchina).")
                ),
                React.createElement("div", { style: styles.leagueInfoCard },
                    React.createElement("h3", { style: styles.leagueInfoTitle }, "Formazione e sostituzioni"),
                    React.createElement("ul", { style: styles.leagueList },
                        React.createElement("li", null, React.createElement("strong", null, "Moduli ammessi:"), " 3-4-3, 3-5-2, 4-3-3, 4-4-2, 4-5-1, 5-3-2, 5-4-1"),
                        React.createElement("li", null, React.createElement("strong", null, "Moduli non ammessi:"), " ", MODULI_NON_AMMESSI.join(", ")),
                        React.createElement("li", null, React.createElement("strong", null, "Sostituzioni massime:"), " 5 per giornata"),
                        React.createElement("li", null, React.createElement("strong", null, "SWAP programmabili:"), " fino a 3"),
                        React.createElement("li", null, React.createElement("strong", null, "Scadenza formazione:"), " 1 minuto prima del fischio d'inizio")
                    ),
                    React.createElement("p", { style: styles.note }, "In caso di mancato invio della formazione, vengono assegnati 66 punti.")
                ),
                React.createElement("div", { style: styles.leagueInfoCard },
                    React.createElement("h3", { style: styles.leagueInfoTitle }, "Bonus e malus principali"),
                    React.createElement("ul", { style: styles.leagueList },
                        React.createElement("li", null, React.createElement("strong", null, "Gol:"), " +3"),
                        React.createElement("li", null, React.createElement("strong", null, "Assist:"), " +1"),
                        React.createElement("li", null, React.createElement("strong", null, "Ammonizione:"), " -0,5"),
                        React.createElement("li", null, React.createElement("strong", null, "Espulsione:"), " -1"),
                        React.createElement("li", null, React.createElement("strong", null, "Portiere imbattuto:"), " +0,5"),
                        React.createElement("li", null, React.createElement("strong", null, "Modificatore difesa:"), " attivo con almeno 4 difensori")
                    ),
                    React.createElement("p", { style: styles.note }, "Il modificatore difesa si calcola su portiere e 3 migliori difensori.")
                )
            )
        );
    }

    function renderSection() {
        if (activeSection === "asta") return renderAsta();
        if (activeSection === "rosa") return renderRosa();
        if (activeSection === "lega") return renderLegaSettings();
        if (activeSection === "formazione") return renderFormazione();
        if (activeSection === "mercato") return renderMercato();
        if (activeSection === "regolamento") return renderRegolamento();
        return renderAsta();
    }

    if (loading) {
        return React.createElement("main", { style: styles.centered },
            React.createElement("h2", null, "Caricamento giocatori 2026/27...")
        );
    }

    if (errorMessage) {
        return React.createElement("main", { style: styles.centered },
            React.createElement("h2", null, "Errore di collegamento"),
            React.createElement("p", null, errorMessage),
            React.createElement("p", null, "Avvia il backend Flask e ricarica questa pagina.")
        );
    }

    return React.createElement("main", { style: styles.page },
        React.createElement("header", { style: styles.header },
            React.createElement("div", null,
                React.createElement("p", { style: styles.eyebrow }, "Fantacalcio personale"),
                React.createElement("h1", { style: styles.title }, nomeLega),
                React.createElement("p", { style: styles.subtitle }, players.length, " giocatori disponibili nel database")
            ),
            React.createElement("div", { style: styles.status },
                React.createElement("span", { style: styles.statusDot }),
                "Backend collegato"
            )
        ),
        React.createElement("nav", { style: styles.navigation },
            SECTIONS.map(function (section) {
                return React.createElement("button", {
                    key: section.id,
                    style: activeSection === section.id ? styles.navButtonActive : styles.navButton,
                    onClick: function () { setActiveSection(section.id); }
                }, section.label);
            })
        ),
        renderSection()
    );
}

var styles = {
    page: {
        minHeight: "100vh",
        padding: "32px",
        backgroundColor: "#f8fafc",
        color: "#0f172a",
        fontFamily: "Arial, sans-serif"
    },
    centered: {
        minHeight: "100vh",
        padding: "32px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        backgroundColor: "#f8fafc",
        color: "#0f172a",
        fontFamily: "Arial, sans-serif"
    },
    header: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "24px",
        marginBottom: "20px"
    },
    eyebrow: {
        margin: "0 0 7px",
        color: "#2563eb",
        fontSize: "12px",
        fontWeight: 700,
        letterSpacing: "1px",
        textTransform: "uppercase"
    },
    title: {
        margin: 0,
        fontSize: "32px"
    },
    subtitle: {
        margin: "8px 0 0",
        color: "#64748b"
    },
    status: {
        display: "flex",
        alignItems: "center",
        gap: "8px",
        padding: "10px 14px",
        borderRadius: "999px",
        backgroundColor: "#dcfce7",
        color: "#166534",
        fontWeight: 700,
        whiteSpace: "nowrap"
    },
    statusDot: {
        width: "9px",
        height: "9px",
        borderRadius: "50%",
        backgroundColor: "#16a34a"
    },
    navigation: {
        display: "flex",
        flexWrap: "wrap",
        gap: "10px",
        marginBottom: "24px",
        paddingBottom: "16px",
        borderBottom: "1px solid #cbd5e1"
    },
    navButton: {
        padding: "10px 14px",
        border: "1px solid #cbd5e1",
        borderRadius: "8px",
        backgroundColor: "#ffffff",
        color: "#334155",
        cursor: "pointer",
        fontWeight: 700
    },
    navButtonActive: {
        padding: "10px 14px",
        border: "1px solid #2563eb",
        borderRadius: "8px",
        backgroundColor: "#2563eb",
        color: "#ffffff",
        cursor: "pointer",
        fontWeight: 700
    },
    filters: {
        display: "flex",
        flexWrap: "wrap",
        gap: "12px",
        padding: "16px",
        border: "1px solid #e2e8f0",
        borderRadius: "14px",
        backgroundColor: "#ffffff"
    },
    input: {
        flex: "1 1 260px",
        padding: "12px",
        border: "1px solid #cbd5e1",
        borderRadius: "8px",
        fontSize: "15px"
    },
    select: {
        padding: "12px",
        border: "1px solid #cbd5e1",
        borderRadius: "8px",
        backgroundColor: "#ffffff",
        fontSize: "15px"
    },
    results: {
        margin: "18px 0",
        color: "#475569"
    },
    tableContainer: {
        overflowX: "auto",
        border: "1px solid #e2e8f0",
        borderRadius: "14px",
        backgroundColor: "#ffffff"
    },
    table: {
        width: "100%",
        minWidth: "1050px",
        borderCollapse: "collapse"
    },
    tableHeader: {
        padding: "13px",
        backgroundColor: "#eff6ff",
        borderBottom: "1px solid #e2e8f0",
        textAlign: "left",
        fontSize: "13px"
    },
    tableCell: {
        padding: "13px",
        borderBottom: "1px solid #e2e8f0"
    },
    playerName: {
        padding: "13px",
        borderBottom: "1px solid #e2e8f0",
        fontWeight: 700
    },
    roleBadge: {
        display: "inline-block",
        minWidth: "28px",
        padding: "5px 7px",
        borderRadius: "6px",
        color: "#ffffff",
        fontSize: "12px",
        fontWeight: 700,
        textAlign: "center"
    },
    roleBadgeSmall: {
        display: "inline-block",
        minWidth: "24px",
        padding: "4px 6px",
        borderRadius: "5px",
        color: "#ffffff",
        fontSize: "11px",
        fontWeight: 700,
        textAlign: "center",
        marginRight: "8px"
    },
    empty: {
        padding: "36px",
        color: "#64748b",
        textAlign: "center"
    },
    pagination: {
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "14px",
        marginTop: "18px"
    },
    button: {
        padding: "10px 14px",
        border: "none",
        borderRadius: "8px",
        backgroundColor: "#2563eb",
        color: "#ffffff",
        cursor: "pointer"
    },
    addButton: {
        padding: "8px 12px",
        border: "none",
        borderRadius: "6px",
        backgroundColor: "#16a34a",
        color: "#ffffff",
        cursor: "pointer",
        fontWeight: 700
    },
    removeButton: {
        padding: "8px 12px",
        border: "none",
        borderRadius: "6px",
        backgroundColor: "#dc2626",
        color: "#ffffff",
        cursor: "pointer",
        fontWeight: 700
    },
    exportRow: {
        marginBottom: "20px"
    },
    exportButton: {
        padding: "10px 14px",
        border: "none",
        borderRadius: "8px",
        backgroundColor: "#0ea5e9",
        color: "#ffffff",
        cursor: "pointer",
        fontWeight: 700
    },
    card: {
        padding: "28px",
        border: "1px solid #e2e8f0",
        borderRadius: "14px",
        backgroundColor: "#ffffff",
        marginBottom: "24px"
    },
    sectionTitle: {
        marginTop: 0,
        marginBottom: "10px",
        fontSize: "25px"
    },
    sectionText: {
        marginTop: 0,
        marginBottom: "24px",
        color: "#475569",
        lineHeight: 1.5
    },
    budgetRow: {
        display: "flex",
        flexWrap: "wrap",
        gap: "24px",
        marginBottom: "20px"
    },
    budgetInput: {
        display: "flex",
        flexDirection: "column",
        gap: "8px"
    },
    budgetLabel: {
        fontSize: "13px",
        color: "#475569"
    },
    budgetField: {
        padding: "10px",
        border: "1px solid #cbd5e1",
        borderRadius: "8px",
        fontSize: "15px",
        width: "180px"
    },
    budgetSummary: {
        display: "flex",
        gap: "24px",
        flexWrap: "wrap"
    },
    budgetItem: {
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        padding: "10px 14px",
        borderRadius: "8px",
        backgroundColor: "#f1f5f9"
    },
    rosterSummary: {
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        marginBottom: "20px"
    },
    rosterTotal: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "14px 16px",
        borderRadius: "8px",
        backgroundColor: "#eff6ff",
        fontSize: "15px"
    },
    rosterFull: {
        padding: "12px 14px",
        borderRadius: "8px",
        backgroundColor: "#fef3c7",
        color: "#78350f",
        fontSize: "14px"
    },
    roleLimitsGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
        gap: "14px",
        marginBottom: "20px"
    },
    roleLimitCard: {
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        padding: "14px",
        border: "1px solid #e2e8f0",
        borderRadius: "10px",
        backgroundColor: "#f8fafc"
    },
    roleLimitLabel: {
        fontSize: "13px",
        color: "#475569"
    },
    roleLimitBar: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between"
    },
    roleLimitValue: {
        fontSize: "18px",
        fontWeight: 700
    },
    statsGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
        gap: "16px"
    },
    statCard: {
        padding: "18px",
        borderRadius: "10px",
        backgroundColor: "#eff6ff"
    },
    statLabel: {
        display: "block",
        marginBottom: "9px",
        color: "#475569",
        fontSize: "13px"
    },
    statValue: {
        fontSize: "22px"
    },
    note: {
        marginTop: "24px",
        padding: "14px",
        borderRadius: "8px",
        backgroundColor: "#fef3c7",
        color: "#78350f"
    },
    formationBox: {
        padding: "20px",
        borderLeft: "5px solid #2563eb",
        borderRadius: "8px",
        backgroundColor: "#eff6ff",
        color: "#1e3a8a"
    },
    marketGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: "18px"
    },
    marketCard: {
        padding: "20px",
        borderRadius: "10px",
        backgroundColor: "#f1f5f9"
    },
    rulesGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: "14px"
    },
    rule: {
        display: "flex",
        flexDirection: "column",
        gap: "7px",
        padding: "15px",
        border: "1px solid #e2e8f0",
        borderRadius: "9px",
        backgroundColor: "#f8fafc"
    },
    moduloRow: {
        display: "flex",
        alignItems: "center",
        gap: "12px",
        marginBottom: "20px"
    },
    moduloLabel: {
        fontSize: "15px",
        fontWeight: 700,
        color: "#334155"
    },
    moduloSelect: {
        padding: "10px",
        border: "1px solid #cbd5e1",
        borderRadius: "8px",
        backgroundColor: "#ffffff",
        fontSize: "15px"
    },
    warningBox: {
        padding: "18px",
        borderLeft: "5px solid #f59e0b",
        borderRadius: "8px",
        backgroundColor: "#fef3c7",
        color: "#78350f"
    },
    summaryBox: {
        display: "flex",
        gap: "18px",
        flexWrap: "wrap",
        marginBottom: "20px"
    },
    summaryItem: {
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        padding: "12px 16px",
        borderRadius: "8px",
        backgroundColor: "#f1f5f9"
    },
    subTitle: {
        marginTop: "24px",
        marginBottom: "12px",
        fontSize: "18px",
        color: "#334155"
    },
    formationGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: "14px"
    },
    playerCard: {
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        padding: "14px",
        border: "1px solid #e2e8f0",
        borderRadius: "10px",
        backgroundColor: "#f8fafc"
    },
    benchList: {
        display: "flex",
        flexDirection: "column",
        gap: "10px"
    },
    benchRow: {
        display: "flex",
        alignItems: "center",
        gap: "10px",
        padding: "10px 12px",
        border: "1px solid #e2e8f0",
        borderRadius: "8px",
        backgroundColor: "#f1f5f9"
    },
    marketNeedsGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
        gap: "14px",
        marginBottom: "20px"
    },
    marketNeedCard: {
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        padding: "14px",
        border: "1px solid #e2e8f0",
        borderRadius: "10px",
        backgroundColor: "#f8fafc"
    },
    marketNeedLabel: {
        fontSize: "13px",
        color: "#475569"
    },
    marketNeedValue: {
        fontSize: "18px",
        fontWeight: 700,
        color: "#166534"
    },
    leagueInfoGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: "18px"
    },
    leagueInfoCard: {
        padding: "20px",
        border: "1px solid #e2e8f0",
        borderRadius: "10px",
        backgroundColor: "#f8fafc"
    },
    leagueInfoTitle: {
        marginTop: 0,
        marginBottom: "12px",
        fontSize: "17px",
        color: "#334155"
    },
    leagueList: {
        margin: 0,
        paddingLeft: "18px",
        color: "#334155",
        lineHeight: 1.6
    },
    legaSettingsGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
        gap: "18px"
    },
    legaSettingCard: {
        padding: "20px",
        border: "1px solid #e2e8f0",
        borderRadius: "10px",
        backgroundColor: "#f8fafc"
    },
    legaSettingTitle: {
        marginTop: 0,
        marginBottom: "14px",
        fontSize: "18px",
        color: "#334155"
    },
    legaInput: {
        width: "100%",
        padding: "10px",
        border: "1px solid #cbd5e1",
        borderRadius: "8px",
        fontSize: "15px",
        marginBottom: "12px"
    },
    legaButton: {
        padding: "10px 14px",
        border: "none",
        borderRadius: "8px",
        backgroundColor: "#2563eb",
        color: "#ffffff",
        cursor: "pointer",
        fontWeight: 700
    },
    vincoliGrid: {
        display: "grid",
        gridTemplateColumns: "1fr",
        gap: "12px",
        marginBottom: "14px"
    },
    vincoloRow: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px"
    },
    vincoloLabel: {
        fontSize: "14px",
        color: "#334155"
    },
    vincoloInput: {
        width: "80px",
        padding: "8px",
        border: "1px solid #cbd5e1",
        borderRadius: "6px",
        fontSize: "14px"
    }
};

export default App;