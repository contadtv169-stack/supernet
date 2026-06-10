const ADMIN_USER = "admin";
const ADMIN_PASS = "Kuronu@SuperNet2026!";

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const u = document.getElementById("username").value;
      const p = document.getElementById("password").value;
      if (u === ADMIN_USER && p === ADMIN_PASS) {
        sessionStorage.setItem("supernet_admin", "1");
        window.location.href = "dashboard.html";
      } else {
        document.getElementById("loginError").classList.remove("hidden");
      }
    });
    if (sessionStorage.getItem("supernet_admin") === "1") {
      window.location.href = "dashboard.html";
    }
  }

  if (window.location.pathname.includes("dashboard.html")) {
    if (sessionStorage.getItem("supernet_admin") !== "1") {
      window.location.href = "login.html";
      return;
    }
    initDashboard();
  }
});

async function apiFetch(endpoint, options = {}) {
  const res = await fetch(`https://api.contadtv169-stack.com${endpoint}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  return res.json();
}

function initDashboard() {
  document.querySelectorAll(".sidebar a[data-page]").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      document.querySelectorAll(".sidebar a").forEach((a) => a.classList.remove("active"));
      link.classList.add("active");
      loadPage(link.dataset.page);
    });
  });
  loadPage("dashboard");
  loadDashboardData();
}

async function loadDashboardData() {
  try {
    const data = { clientes: 0, vendasHoje: 0, faturamento: 0, saldo: 0 };
    document.getElementById("clientesAtivos").textContent = data.clientes;
    document.getElementById("vendasHoje").textContent = `R$ ${data.vendasHoje.toFixed(2)}`;
    document.getElementById("faturamentoMensal").textContent = `R$ ${data.faturamento.toFixed(2)}`;
    document.getElementById("saldoKrypt").textContent = `R$ ${data.saldo.toFixed(2)}`;
  } catch (e) {
    console.error("Erro ao carregar dados:", e);
  }
}

function loadPage(page) {
  const title = document.getElementById("pageTitle");
  const container = document.getElementById("tablesContainer");
  title.textContent = page.charAt(0).toUpperCase() + page.slice(1);
  const pages = {
    dashboard: "<p>Bem-vindo ao painel SuperNet. Selecione um modulo ao lado.</p>",
    clientes: gerarTabela(["ID", "Nome", "Discord", "Plano", "Status", "Expira", "Acoes"], []),
    pagamentos: gerarTabela(["ID Tx", "Cliente", "Valor", "Metodo", "Status", "Data"], []),
    saques: `
      <h3>Metodos de Saque</h3>
      <ul>
        <li>PIX (CPF/CNPJ/EMAIL/PHONE)</li>
        <li>USDT TRC20</li>
      </ul>
      <p>Use /admin saque no Discord para solicitar.</p>`,
    logs: "<p>Logs serao exibidos aqui apos configuracao.</p>",
    config: `
      <h3>Configuracoes</h3>
      <form id="configForm">
        <label>Gateway CI: <input type="text" value="krypt_ci_49e0355123ad4d54fa" /></label><br/>
        <label>Gateway CS: <input type="text" value="krypt_cs_952dfe7561989e86e889204c1f1ab313" /></label><br/>
        <label>Servidor IP: <input type="text" value="162.120.186.147" /></label><br/>
        <button type="submit" class="btn">Salvar</button>
      </form>`,
  };
  container.innerHTML = pages[page] || "<p>Pagina nao encontrada</p>";
}

function gerarTabela(colunas, linhas) {
  let html = "<table><thead><tr>";
  colunas.forEach((c) => (html += `<th>${c}</th>`));
  html += "</tr></thead><tbody>";
  if (linhas.length === 0) {
    html += `<tr><td colspan="${colunas.length}">Nenhum registro encontrado</td></tr>`;
  }
  linhas.forEach((linha) => {
    html += "<tr>";
    linha.forEach((celula) => (html += `<td>${celula}</td>`));
    html += "</tr>";
  });
  html += "</tbody></table>";
  return html;
}
