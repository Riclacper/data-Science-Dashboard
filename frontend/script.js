const API = 'http://127.0.0.1:5000';

async function carregarCasos() {
  const res = await fetch(`${API}/casos`);
  const dados = await res.json();

  const filtro = document.getElementById("filtro").value;
  const filtrados = filtro ? dados.filter(c => c.tipoCrime === filtro) : dados;

  const porTipo = {};

  if (filtro) {
    porTipo[filtro] = filtrados.length;
  } else {
    filtrados.forEach(c => {
      porTipo[c.tipoCrime] = (porTipo[c.tipoCrime] || 0) + 1;
    });
  }

  const ctx = document.getElementById('grafico').getContext('2d');

  if (window.graficoCasos instanceof Chart) {
    window.graficoCasos.destroy();
  }

  window.graficoCasos = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Object.keys(porTipo),
      datasets: [{
        label: 'Ocorrências por tipo',
        data: Object.values(porTipo),
        backgroundColor: '#4B6584'
      }]
    },
    options: {
      responsive: true,
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.raw}`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: {
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
            font: {
              size: 12
            }
          }
        },
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

async function preencherFiltroTipos() {
  const res = await fetch(`${API}/casos`);
  const dados = await res.json();
  const tiposUnicos = [...new Set(dados.map(c => c.tipoCrime))].sort();

  const select = document.getElementById("filtro");
  select.innerHTML = '<option value="">Todos</option>'; // resetar

  tiposUnicos.forEach(tipo => {
    const option = document.createElement("option");
    option.value = tipo;
    option.textContent = tipo;
    select.appendChild(option);
  });
}

async function carregarFeatures() {
  const res = await fetch(`${API}/features`);
  const dados = await res.json();

  const labelsLegiveis = dados.features.map(f => {
    switch (f) {
      case "tipoCrime": return "Tipo de Crime";
      case "cidade": return "Cidade";
      case "uf": return "Estado (UF)";
      case "hora_num": return "Hora da Ocorrência";
      default: return f;
    }
  });

  const ctx = document.getElementById('graficoFeatures').getContext('2d');

  if (window.graficoFeatures instanceof Chart) {
    window.graficoFeatures.destroy();
  }

  window.graficoFeatures = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labelsLegiveis,
      datasets: [{
        label: 'Fatores que mais influenciam o modelo',
        data: dados.importances.map(i => +(i * 100).toFixed(2)),
        backgroundColor: '#7B1FA2'
      }]
    },
    options: {
      responsive: true,
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.raw}%`;
            }
          }
        },
        title: {
          display: false
        }
      },
      scales: {
        y: {
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          }
        }
      }
    }
  });
}

async function predizer() {
  const tipoCrime = document.getElementById('tipoCrime').value;
  const cidade = document.getElementById('cidade').value;
  const uf = document.getElementById('uf').value;
  const hora = document.getElementById('hora').value;

  const r = await fetch(`${API}/predict`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ tipoCrime, cidade, uf, hora })
  });

  const res = await r.json();
  document.getElementById('resposta').innerText =
    res.previsao_status ? `Previsão: ${res.previsao_status}` : `Erro: ${res.erro}`;
}


function exportarCSV() {
  fetch(`${API}/casos`)
    .then(response => response.json())
    .then(dados => {
      const filtro = document.getElementById("filtro").value;
      const filtrados = filtro ? dados.filter(c => c.natureza === filtro) : dados;

      if (filtrados.length === 0) {
        alert("Nenhum dado disponível para exportar.");
        return;
      }

      const headers = Object.keys(filtrados[0]);
      const csv = [
        headers.join(","),
        ...filtrados.map(obj => headers.map(h => `"${(obj[h] || "").toString().replace(/"/g, '""')}"`).join(","))
      ].join("\n");

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "casos_exportados.csv";
      link.style.display = "none";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
}

function logout() {
  localStorage.removeItem('usuario_logado');
  window.location.href = 'login.html';
}

async function carregarAvaliacao() {
  const [avaliacaoRes, classesRes] = await Promise.all([
    fetch(`${API}/avaliar-modelo`),
    fetch(`${API}/classes`)
  ]);

  const data = await avaliacaoRes.json();
  const classeLabels = await classesRes.json();

  const tbody = document.querySelector("#tabelaAvaliacao tbody");
  tbody.innerHTML = "";

  for (const classe in data) {
    if (["accuracy", "macro avg", "weighted avg"].includes(classe)) continue;

    const dadosClasse = data[classe];
    if (!dadosClasse || typeof dadosClasse !== "object") continue;

    const nomeClasse = classeLabels[classe] || classe;
    const f1 = dadosClasse["f1-score"] ?? 0;
    const precision = dadosClasse["precision"] ?? 0;
    const recall = dadosClasse["recall"] ?? 0;
    const support = dadosClasse["support"] ?? 0;

    const linha = document.createElement("tr");
    const celulas = [
      nomeClasse,
      (f1 * 100).toFixed(0) + '%',
      (precision * 100).toFixed(0) + '%',
      (recall * 100).toFixed(0) + '%',
      support
    ];

    celulas.forEach(valor => {
      const td = document.createElement("td");
      td.textContent = valor;
      linha.appendChild(td);
    });

    tbody.appendChild(linha);
  }
}


async function graficoMetricasModelo() {
  const [avaliacaoRes, classesRes] = await Promise.all([
    fetch(`${API}/avaliar-modelo`),
    fetch(`${API}/classes`)
  ]);

  const data = await avaliacaoRes.json();
  const classeLabels = await classesRes.json();

  const classes = [];
  const f1Scores = [];
  const precisions = [];
  const recalls = [];

  for (const classe in data) {
    if (["accuracy", "macro avg", "weighted avg"].includes(classe)) continue;
    if (!data[classe]["f1-score"]) continue;

    classes.push(classeLabels[classe] || classe);
    f1Scores.push(data[classe]["f1-score"] * 100);
    precisions.push(data[classe]["precision"] * 100);
    recalls.push(data[classe]["recall"] * 100);
  }

  const ctx = document.getElementById("graficoMetricas").getContext("2d");
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: classes,
      datasets: [
        {
          label: "Desempenho Geral (%)",
          data: f1Scores,
          backgroundColor: "#5DADE2"
        },
        {
          label: "Acerto (%)",
          data: precisions,
          backgroundColor: "#F5B041"
        },
        {
          label: "Cobertura (%)",
          data: recalls,
          backgroundColor: "#AF7AC5"
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: {
          display: true,
          text: "Comparativo de Métricas por Classe"
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.raw.toFixed(0)}%`;
            }
          }
        }
      },
      scales: {
        y: {
          ticks: {
            callback: function(value) {
              return value + '%';
            },
            beginAtZero: true,
            max: 100
          }
        }
      }
    }
  });
}


async function graficoRadarMetricas() {
  const [avaliacaoRes, classesRes] = await Promise.all([
    fetch(`${API}/avaliar-modelo`),
    fetch(`${API}/classes`)
  ]);

  const data = await avaliacaoRes.json();
  const classeLabels = await classesRes.json();

  const labels = [];
  const f1 = [];
  const precision = [];
  const recall = [];

  for (const key in data) {
    if (!data[key]["f1-score"]) continue;
    if (["accuracy", "macro avg", "weighted avg"].includes(key)) continue;

    labels.push(classeLabels[key] || key);
    f1.push(data[key]["f1-score"] * 100);
    precision.push(data[key]["precision"] * 100);
    recall.push(data[key]["recall"] * 100);
  }

  const ctx = document.getElementById("graficoRadarMetricas").getContext("2d");
  new Chart(ctx, {
    type: "radar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Desempenho Geral (%)",
          data: f1,
          fill: true,
          backgroundColor: "rgba(93, 173, 226, 0.2)",
          borderColor: "rgba(93, 173, 226, 1)",
          pointBackgroundColor: "rgba(93, 173, 226, 1)"
        },
        {
          label: "Acerto (%)",
          data: precision,
          fill: true,
          backgroundColor: "rgba(245, 176, 65, 0.2)",
          borderColor: "rgba(245, 176, 65, 1)",
          pointBackgroundColor: "rgba(245, 176, 65, 1)"
        },
        {
          label: "Cobertura (%)",
          data: recall,
          fill: true,
          backgroundColor: "rgba(175, 122, 197, 0.2)",
          borderColor: "rgba(175, 122, 197, 1)",
          pointBackgroundColor: "rgba(175, 122, 197, 1)"
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: "Comparação de Desempenho por Classe"
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.raw.toFixed(0)}%`;
            }
          }
        }
      },
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: {
            callback: value => value + "%"
          }
        }
      }
    }
  });
}

async function enviarRelatorio() {
  const email = document.getElementById("emailDestino").value;

  if (!email.includes("@")) {
    document.getElementById("statusEnvio").innerText = "E-mail inválido.";
    return;
  }

  const res = await fetch(`${API}/enviar-relatorio`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });

  const resultado = await res.json();
  document.getElementById("statusEnvio").innerText = resultado.msg || resultado.erro;
}

carregarCasos();
carregarFeatures();
carregarAvaliacao();
graficoMetricasModelo();
graficoRadarMetricas();
preencherFiltroTipos();
