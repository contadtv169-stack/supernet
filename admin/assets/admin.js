const ADMIN_USER = "admin";
const ADMIN_PASS = "Kuronu@SuperNet2026!";
let usuariosCache = [];

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
      window.location.href = "login.html"; return;
    }
    initDashboard();
  }
});

function toast(msg, type = "success") {
  const t = document.createElement("div");
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
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
}

async function apiGet(endpoint) {
  try {
    const r = await fetch(`https://api.contadtv169-stack.com${endpoint}`);
    return await r.json();
  } catch { return null; }
}

function loadPage(page) {
  const title = document.getElementById("pageTitle");
  const container = document.getElementById("pageContent");
  title.textContent = page.charAt(0).toUpperCase() + page.slice(1);

  if (page === "dashboard") renderDashboard(container);
  else if (page === "usuarios") renderUsuarios(container);
  else if (page === "vendas") renderVendas(container);
  else if (page === "pagamentos") renderPagamentos(container);
  else if (page === "saques") renderSaques(container);
  else if (page === "logs") renderLogs(container);
  else if (page === "config") renderConfig(container);
}

function renderDashboard(el) {
  const usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  const ativos = usuarios.filter(u => u.status === "ativo").length;
  const vendasHoje = 0;
  const fatMensal = usuarios.reduce((s, u) => s + (u.plano === "premium" ? 39.9 : 19.9), 0);
  el.innerHTML = `
    <div class="widgets">
      <div class="widget"><h3>Usuarios Ativos</h3><p id="wAtivos">${ativos}</p><div class="sub">Total: ${usuarios.length}</div></div>
      <div class="widget"><h3>Vendas Hoje</h3><p>R$ ${vendasHoje.toFixed(2)}</p></div>
      <div class="widget"><h3>Faturamento Mensal</h3><p>R$ ${fatMensal.toFixed(2)}</p></div>
      <div class="widget"><h3>Saldo Krypt</h3><p>R$ 0,00</p></div>
    </div>
    <h3 style="margin-top:20px;">Ultimos Usuarios</h3>
    ${gerarTabelaUsuarios(usuarios.slice(-5).reverse())}
  `;
}

function renderUsuarios(el) {
  let usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  usuariosCache = usuarios;
  el.innerHTML = `
    <div style="display:flex;gap:10px;margin-bottom:15px;flex-wrap:wrap;">
      <button class="btn btn-sm" onclick="abrirModalCriar()">+ Novo Usuario</button>
      <button class="btn btn-sm btn-warning" onclick="exportarUsuarios()">Exportar CSV</button>
      <input type="text" id="filtroUser" placeholder="Buscar..." oninput="filtrarUsuarios()" style="padding:8px 12px;border:1px solid #2a2a4a;border-radius:6px;background:#0a0a0a;color:#fff;outline:none;" />
    </div>
    <div id="tabelaUsuarios">${gerarTabelaUsuarios(usuarios.reverse())}</div>
  `;
}

function filtrarUsuarios() {
  const q = document.getElementById("filtroUser").value.toLowerCase();
  const usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  const filtrados = q ? usuarios.filter(u => u.nome?.toLowerCase().includes(q) || u.discord?.toLowerCase().includes(q) || u.login?.toLowerCase().includes(q)) : usuarios;
  document.getElementById("tabelaUsuarios").innerHTML = gerarTabelaUsuarios(filtrados.reverse());
}

function gerarTabelaUsuarios(lista) {
  if (!lista.length) return "<p style='color:#666;margin-top:20px;'>Nenhum usuario cadastrado.</p>";
  let html = `<table><thead><tr>
    <th>ID</th><th>Nome</th><th>Discord</th><th>Login</th><th>Plano</th><th>Status</th><th>Expira</th><th>Acoes</th>
  </tr></thead><tbody>`;
  lista.forEach(u => {
    const statusClass = u.status === "ativo" ? "badge-ativo" : u.status === "expirado" ? "badge-expirado" : "badge-bloqueado";
    html += `<tr>
      <td>${u.id || "-"}</td>
      <td>${u.nome || "-"}</td>
      <td>${u.discord || "-"}</td>
      <td style="font-family:monospace;font-size:0.8rem;">${u.login || "-"}</td>
      <td>${u.plano === "premium" ? "Premium" : "Basico"}</td>
      <td><span class="badge ${statusClass}">${u.status}</span></td>
      <td style="font-size:0.85rem;">${u.expira || "-"}</td>
      <td>
        <button class="btn btn-sm" onclick="verUsuario('${u.id}')">Ver</button>
        ${u.status === "ativo" ? `<button class="btn btn-sm btn-danger" onclick="bloquearUser('${u.id}')">Bloquear</button>` : `<button class="btn btn-sm btn-success" onclick="desbloquearUser('${u.id}')">Desbloq</button>`}
        <button class="btn btn-sm btn-danger" onclick="excluirUser('${u.id}')">Excluir</button>
      </td>
    </tr>`;
  });
  html += "</tbody></table>";
  return html;
}

function abrirModalCriar() {
  const el = document.getElementById("modalCriar");
  if (el) el.remove();
  const d = document.createElement("div");
  d.id = "modalCriar";
  d.className = "modal show";
  d.innerHTML = `
    <div class="modal-content">
      <button class="modal-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
      <h3>Criar Usuario</h3>
      <div class="form-group"><label>Nome</label><input id="fNome" placeholder="Nome do cliente" /></div>
      <div class="form-group"><label>Discord ID</label><input id="fDiscord" placeholder="ID do Discord" /></div>
      <div class="form-group"><label>Plano</label><select id="fPlano"><option value="basico">Basico - R$19,90</option><option value="premium">Premium - R$39,90</option></select></div>
      <div class="form-group"><label>Dias</label><input id="fDias" type="number" value="30" /></div>
      <button class="btn" onclick="criarUsuario()">Criar Usuario</button>
    </div>
  `;
  document.body.appendChild(d);
}

function criarUsuario() {
  const nome = document.getElementById("fNome").value || "Cliente";
  const discord = document.getElementById("fDiscord").value || "0";
  const plano = document.getElementById("fPlano").value;
  const dias = parseInt(document.getElementById("fDias").value) || 30;
  const login = "SN" + Math.random().toString(36).substring(2, 8).toUpperCase();
  const senha = Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 10);
  const usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  const id = String(usuarios.length + 1).padStart(4, "0");
  const expira = new Date(Date.now() + dias * 86400000).toISOString().split("T")[0];
  usuarios.push({ id, nome, discord, login, senha, plano, status: "ativo", expira, criado: new Date().toISOString() });
  localStorage.setItem("supernet_usuarios", JSON.stringify(usuarios));
  document.getElementById("modalCriar").remove();
  toast("Usuario criado! Login: " + login);
  loadPage("usuarios");
}

function verUsuario(id) {
  const usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  const u = usuarios.find(x => x.id === id);
  if (!u) return toast("Usuario nao encontrado", "error");
  const d = document.createElement("div");
  d.className = "modal show";
  d.innerHTML = `
    <div class="modal-content">
      <button class="modal-close" onclick="this.parentElement.remove()">&times;</button>
      <h3>Usuario #${u.id}</h3>
      <p><strong>Nome:</strong> ${u.nome}</p>
      <p><strong>Discord:</strong> ${u.discord}</p>
      <p><strong>Plano:</strong> ${u.plano === "premium" ? "Premium" : "Basico"}</p>
      <p><strong>Status:</strong> ${u.status}</p>
      <p><strong>Expira:</strong> ${u.expira}</p>
      <h4 style="margin-top:15px;color:#00d4ff;">Credenciais de Acesso</h4>
      <pre id="credText">Login: ${u.login}
Senha: ${u.senha}
Servidor: 162.120.186.147
Porta: 51820 (WireGuard)
Proxy: 162.120.186.147:8080
Metodo: WireGuard + DPI Bypass
Expira: ${u.expira}</pre>
      <button class="btn btn-sm" onclick="copiarCred('${u.id}')">Copiar Credenciais</button>
    </div>
  `;
  d.id = "modalVer";
  document.body.appendChild(d);
}

function copiarCred(id) {
  const usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  const u = usuarios.find(x => x.id === id);
  if (!u) return;
  const txt = `Login: ${u.login}\nSenha: ${u.senha}\nServidor: 162.120.186.147\nPorta: 51820 (WireGuard)\nProxy: 162.120.186.147:8080\nMetodo: WireGuard + DPI Bypass\nExpira: ${u.expira}`;
  navigator.clipboard.writeText(txt).then(() => toast("Credenciais copiadas!"));
}

function bloquearUser(id) {
  let usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  const idx = usuarios.findIndex(x => x.id === id);
  if (idx >= 0) { usuarios[idx].status = "bloqueado"; localStorage.setItem("supernet_usuarios", JSON.stringify(usuarios)); toast("Usuario bloqueado"); loadPage("usuarios"); }
}

function desbloquearUser(id) {
  let usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  const idx = usuarios.findIndex(x => x.id === id);
  if (idx >= 0) { usuarios[idx].status = "ativo"; localStorage.setItem("supernet_usuarios", JSON.stringify(usuarios)); toast("Usuario desbloqueado"); loadPage("usuarios"); }
}

function excluirUser(id) {
  if (!confirm("Excluir usuario #" + id + "?")) return;
  let usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  usuarios = usuarios.filter(x => x.id !== id);
  localStorage.setItem("supernet_usuarios", JSON.stringify(usuarios));
  toast("Usuario excluido");
  loadPage("usuarios");
}

function exportarUsuarios() {
  const usuarios = JSON.parse(localStorage.getItem("supernet_usuarios") || "[]");
  let csv = "ID,Nome,Discord,Login,Senha,Plano,Status,Expira\n";
  usuarios.forEach(u => { csv += `${u.id},"${u.nome}","${u.discord}",${u.login},${u.senha},${u.plano},${u.status},${u.expira}\n`; });
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = url; a.download = "supernet_usuarios.csv"; a.click();
  URL.revokeObjectURL(url);
  toast("CSV exportado");
}

function renderVendas(el) {
  el.innerHTML = `<p>Grafico de vendas em breve.</p>`;
}

function renderPagamentos(el) {
  el.innerHTML = `<p>Historico de pagamentos via Krypt Gateway.</p>`;
}

function renderSaques(el) {
  el.innerHTML = `
    <h3>Metodos de Saque</h3>
    <ul style="margin:15px 0 0 20px;color:#ccc;">
      <li>PIX (CPF / CNPJ / EMAIL / PHONE)</li>
      <li>USDT TRC20</li>
    </ul>
    <p style="margin-top:15px;color:#888;">Use o comando <code style="background:#1a1a2e;padding:2px 6px;border-radius:4px;">/admin saque</code> no Discord.</p>
  `;
}

function renderLogs(el) {
  const logs = JSON.parse(localStorage.getItem("supernet_logs") || "[]");
  el.innerHTML = logs.length ? logs.map(l => `<div style="padding:6px 0;border-bottom:1px solid #222;font-size:0.85rem;font-family:monospace;color:#888;">${l}</div>`).join("") : "<p style='color:#666;'>Nenhum log registrado.</p>";
}

function renderConfig(el) {
  el.innerHTML = `
    <h3>Configuracoes do Sistema</h3>
    <div class="form-group"><label>Gateway CI</label><input id="cfgCI" value="krypt_ci_49e0355123ad4d54fa" /></div>
    <div class="form-group"><label>Gateway CS</label><input id="cfgCS" value="krypt_cs_952dfe7561989e86e889204c1f1ab313" /></div>
    <div class="form-group"><label>Servidor IP</label><input id="cfgIP" value="162.120.186.147" /></div>
    <div class="form-group"><label>Discord Token</label><input id="cfgToken" value="MTUxNDI3NTU4Mjc0NDE5OTM4OA.GwmhpG.c4NXR-Y-98BY1Ez2bWBsyQCpQ0wkpSlFOqs-3g" type="password" /></div>
    <div class="form-group"><label>Guild ID</label><input id="cfgGuild" value="1514275582744199388" /></div>
    <button class="btn" onclick="salvarConfig()">Salvar</button>
    <p id="cfgMsg" class="success hidden" style="margin-top:10px;">Configuracoes salvas!</p>
  `;
}

function salvarConfig() {
  const cfg = {
    ci: document.getElementById("cfgCI").value,
    cs: document.getElementById("cfgCS").value,
    ip: document.getElementById("cfgIP").value,
    token: document.getElementById("cfgToken").value,
    guild: document.getElementById("cfgGuild").value,
  };
  localStorage.setItem("supernet_config", JSON.stringify(cfg));
  document.getElementById("cfgMsg").classList.remove("hidden");
  setTimeout(() => document.getElementById("cfgMsg").classList.add("hidden"), 3000);
}
