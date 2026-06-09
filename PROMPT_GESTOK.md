# PROMPT MASTER — GESTOK
## Portal de Gestão de Inventário e Vendas

---

## CONTEXTO
Desenvolva uma aplicação chamada **Gestok**, um sistema de **PDV (Ponto de Venda) simplificado para pequenos comércios**, seguindo obrigatoriamente o padrão **Class Based View (CBV)**.


## STACK OBRIGATÓRIA

**Backend:**
- Python 3.12+
- Django 5+
- Django REST Framework
- MySQL / MariaDB

**Frontend:**
- Bootstrap 5.3
- Bootstrap Icons 1.11+
- Chart.js 4+
- CSS customizado via arquivo `static/css/gestok.css`

**API:**
- Desenvolver um API completa para o catálogo de produtos para integração com o front end e com suporte para um futuro integração em aplicação com react e mobile

---

## ESTRUTURA DO PROJETO

```
gestok/
├── accounts/
├── products/
├── sales/
├── cashier/
├── reports/
├── api/
├── core/
├── templates/
│   ├── base.html
│   ├── base_auth.html
│   ├── components/
│   │   ├── sidebar.html
│   │   ├── topbar.html
│   │   ├── alerts.html
│   │   └── pagination.html
│   ├── accounts/
│   ├── products/
│   ├── sales/
│   ├── cashier/
│   ├── reports/
│   └── dashboard/
└── static/
    ├── css/
    │   └── gestok.css
    └── js/
        └── gestok.js
```

---

## REQUISITOS OBRIGATÓRIOS DO PROFESSOR

- Sistema de PDV simplificado
- Utilização de Class Based Views
- Controle de estoque com alerta de estoque baixo
- Registro de vendas com Django Formsets ou CBVs encadeadas
- Relatório de fechamento de caixa diário
- Gráfico anual de vendas para análise de sazonalidade
- API completa para catálogo de produtos
- Controle rigoroso de permissões
- Apenas administradores podem alterar preços
- Apenas administradores podem realizar estornos

---

# MÓDULO DE FRONTEND

## IDENTIDADE VISUAL

Definir uma paleta de cores consistente e profissional no arquivo `gestok.css`:

```css
:root {
  --gestok-primary:     #2563EB;
  --gestok-primary-dark:#1D4ED8;
  --gestok-secondary:   #64748B;
  --gestok-success:     #16A34A;
  --gestok-danger:      #DC2626;
  --gestok-warning:     #D97706;
  --gestok-info:        #0891B2;
  --gestok-light:       #F8FAFC;
  --gestok-dark:        #0F172A;
  --gestok-sidebar-bg:  #1E293B;
  --gestok-sidebar-w:   260px;
  --gestok-topbar-h:    60px;
}
```

Tipografia padrão: `Inter`, fallback `system-ui, sans-serif`. Importar via Google Fonts no `base.html`.

---

## LAYOUT PRINCIPAL — `base.html`

Criar um layout de três zonas:

```
┌──────────────────────────────────────────────────────┐
│                    TOPBAR (60px)                      │
├────────────────┬─────────────────────────────────────┤
│                │                                     │
│   SIDEBAR      │         MAIN CONTENT                │
│   (260px)      │         (flex: 1)                   │
│                │                                     │
└────────────────┴─────────────────────────────────────┘
```

Requisitos do layout:

- Sidebar fixa à esquerda, com scroll interno independente
- Topbar fixa no topo com z-index elevado
- Conteúdo principal com `margin-left: var(--gestok-sidebar-w)` e `padding-top: var(--gestok-topbar-h)`
- Layout 100% responsivo: sidebar se recolhe em telas menores que 768px (offcanvas Bootstrap)
- Usar `d-flex`, `flex-column`, `vh-100` do Bootstrap para estrutura base

---

## SIDEBAR

A sidebar deve ser dinâmica e refletir o perfil do usuário logado.

**Estrutura visual:**

```
┌──────────────────────┐
│  [Logo Gestok]       │
│  SISTEMA DE VENDAS   │
├──────────────────────┤
│  Dashboard           │
├──────────────────────┤
│  VENDAS              │
│  > Nova Venda        │
│  > Minhas Vendas     │
├──────────────────────┤
│  ESTOQUE             │
│  > Produtos          │
│  > Movimentações     │
├──────────────────────┤
│  CAIXA               │
│  > Tela de Caixa     │
├──────────────────────┤
│  RELATÓRIOS (adm.)   │
│  > Fechamento Caixa  │
│  > Vendas Anuais     │
├──────────────────────┤
│  USUÁRIOS (adm.)     │
│  > Listar Usuários   │
│  > Cadastrar         │
│  > Inativos          │
├──────────────────────┤
│  [Avatar] Nome       │
│  Perfil · Cargo      │
│  [Sair]              │
└──────────────────────┘
```

Regras:

- Itens de menu exibidos com `{% if user.profile == 'ADMINISTRADOR' %}` (ou equivalente com grupos Django)
- Item ativo destacado com cor `--gestok-primary` e fundo levemente opaco
- Ícones Bootstrap Icons em todos os itens (ex.: `bi-speedometer2`, `bi-cart3`, `bi-box-seam`)
- Grupos de menu com separador visual e label de seção em uppercase pequeno
- Área de perfil do usuário no rodapé da sidebar com avatar gerado por iniciais (CSS)

---

## TOPBAR

```
┌────────────────────────────────────────────────────────────┐
│ [≡ Toggle]  Gestok         [🔔 Alertas]  [👤 Nome ▾]      │
└────────────────────────────────────────────────────────────┘
```

Requisitos:

- Botão hambúrguer para toggle da sidebar em mobile
- Badge vermelho no ícone de alertas quando houver produtos com estoque crítico (`estoque_atual <= estoque_minimo`)
- Dropdown do usuário com: Ver Perfil, Alterar Senha, Sair
- Breadcrumb dinâmico abaixo do topbar (opcional mas desejável)

---

## TEMPLATES DE AUTENTICAÇÃO — `base_auth.html`

Criar template separado para telas de login e troca de senha.

Layout centralizado tipo "card no centro da tela":

```
┌─────────────────────────────────────┐
│                                     │
│      [Logo Gestok]                  │
│      Sistema de Vendas              │
│                                     │
│  ┌───────────────────────────────┐  │
│  │     Login                     │  │
│  │   Matrícula: [__________]     │  │
│  │   Senha:     [__________]     │  │
│  │                               │  │
│  │   [  Entrar  ]                │  │
│  └───────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

- Fundo com cor `--gestok-dark` ou gradiente sutil
- Card com `box-shadow` médio, `border-radius: 12px`
- Inputs com ícones dentro (`bi-person`, `bi-lock`)
- Mensagens de erro exibidas com `alert alert-danger`
- Animação de entrada do card: `fadeIn` com CSS simples

---

## DASHBOARD — ADMINISTRADOR

Organizar em grid de cards com métricas e gráfico:

```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Produtos │ │ Críticos │ │Vendas/Dia│ │ Fat./Dia │
│   142    │ │  🔴  8   │ │   23     │ │ R$4.520  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

┌────────────────────────────────────────────────────┐
│  Vendas Mensais — 2025  [Filtro Ano ▾]            │
│  Chart.js — Bar Chart com 12 meses                │
│  Legenda: ✦ Melhor mês  ✦ Pior mês                │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  Últimas Vendas                                    │
│  VEN-000001 · João · R$120,00 · FINALIZADA 🟢     │
│  VEN-000002 · Ana  · R$80,00  · ABERTA    🟡      │
└────────────────────────────────────────────────────┘
```

Cards de métricas:

- Usar `card` Bootstrap com ícone grande, valor em destaque, label abaixo
- Card "Estoque Crítico" com borda e badge vermelho quando valor > 0
- Cards clicáveis: redirecionar para a seção correspondente

---

## DASHBOARD — CAIXA

```
┌────────────────────────────────────┐
│ Vendas abertas: 5                  │
│ [Ver tela de caixa →]              │
└────────────────────────────────────┘
┌────────────────────────────────────┐
│ Minhas finalizadas hoje: 12        │
│ Total vendido: R$ 1.840,00         │
└────────────────────────────────────┘
```

---

## DASHBOARD — VENDAS

```
┌──────────────────────────────────────────────────┐
│ Produtos disponíveis: 130   Estoque crítico: 8   │
└──────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────┐
│ Minhas vendas abertas:                           │
│  VEN-000010 · 3 itens · R$210,00                │
│  [Adicionar itens]  [Ver detalhes]               │
└──────────────────────────────────────────────────┘
```

---

## TELA DE NOVA VENDA (PERFIL VENDAS)

Implementar com Django Formset inline:

```
Nova Venda
─────────────────────────────────────────────────

  Produto         Qtd    Preço Unit.    Subtotal
  [Select ▾]      [1]    R$ 0,00        R$ 0,00     [🗑]
  [+ Adicionar item]

─────────────────────────────────────────────────
                              Total:  R$ 0,00

                     [ Criar Venda Aberta ]
```

Requisitos visuais:

- Tabela responsiva com `table-striped table-hover`
- Select de produto com busca (usar Select2 ou `<datalist>`)
- Preço unitário preenchido automaticamente via fetch/AJAX ao selecionar produto
- Subtotal calculado em tempo real via JavaScript (`gestok.js`)
- Total geral atualizado dinamicamente
- Botão "Adicionar item" insere nova linha ao formset (JavaScript + management_form)
- Botão remover linha com ícone `bi-trash`
- Validações inline: quantidade <= 0 destaca campo em vermelho

---

## TELA DE CAIXA (CAIXA / ADMINISTRADOR)

```
┌──────────────────────────────────────────────────────────┐
│  Vendas Abertas                                          │
│                                                          │
│  VEN-000010  João Silva   3 itens  R$210,00  [Abrir ▸]  │
│  VEN-000011  Ana Lima     1 item   R$80,00   [Abrir ▸]  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Detalhes — VEN-000010                                   │
│                                                          │
│  Produto A    2x  R$50,00    R$100,00                    │
│  Produto B    1x  R$110,00   R$110,00                    │
│                              ─────────                   │
│                   Total:     R$210,00                    │
│                                                          │
│  Forma de pagamento: ● Dinheiro  ○ Pix  ○ Cartão        │
│                                                          │
│  [ Finalizar Venda ]                                     │
└──────────────────────────────────────────────────────────┘
```

Requisitos visuais:

- Painel de duas colunas: lista à esquerda, detalhes à direita
- Venda selecionada destacada com borda `--gestok-primary`
- Botões de forma de pagamento como `btn-check` Bootstrap (radio visual)
- Confirmação antes de finalizar: modal Bootstrap com resumo
- Após finalização: atualizar lista automaticamente (JS ou redirect com mensagem)
- Badge de status: `ABERTA` (amarelo), `FINALIZADA` (verde), `ESTORNADA` (vermelho)

---

## TELA DE ESTORNO (ADMINISTRADOR)

```
┌────────────────────────────────────────────────────┐
│ Estornar Venda                                     │
│                                                    │
│ Número: [VEN-000010    ]  [Buscar]                 │
│                                                    │
│ Vendedor: João Silva  Data: 05/06/2025             │
│ Itens: 3              Total: R$ 210,00             │
│ Status: FINALIZADA ✅                              │
│                                                    │
│ Motivo do estorno (obrigatório):                   │
│ [___________________________________]              │
│                                                    │
│ [ Confirmar Estorno ]   [ Cancelar ]               │
└────────────────────────────────────────────────────┘
```

- Botão "Confirmar Estorno" exige confirmação via modal Bootstrap
- Campo motivo é `required` com validação visual
- Exibir alerta de sucesso/erro após ação com `messages` Django
- Acesso restrito por decorator/mixin: apenas `ADMINISTRADOR`

---

## ALERTAS E MENSAGENS DO SISTEMA

Criar componente `components/alerts.html` incluído no `base.html`:

```django
{% for message in messages %}
<div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
  <i class="bi bi-{{ icon }}"></i> {{ message }}
  <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
{% endfor %}
```

Mapear tags Django → Bootstrap + ícone:

| Django tag | Bootstrap class  | Ícone Bootstrap Icons     |
|------------|------------------|---------------------------|
| `success`  | `alert-success`  | `bi-check-circle-fill`    |
| `error`    | `alert-danger`   | `bi-x-circle-fill`        |
| `warning`  | `alert-warning`  | `bi-exclamation-triangle` |
| `info`     | `alert-info`     | `bi-info-circle-fill`     |

---

## GRÁFICO ANUAL DE VENDAS

Implementar com Chart.js no template `reports/vendas_anuais.html`:

```javascript
// gestok.js
const ctx = document.getElementById('chartVendasAnuais').getContext('2d');
const chart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'],
    datasets: [{
      label: 'Faturamento mensal',
      data: [...],  // injetados via template Django
      backgroundColor: [...],  // melhor mês = verde, pior mês = vermelho, demais = azul
      borderRadius: 6,
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => `R$ ${ctx.raw.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`
        }
      }
    },
    scales: {
      y: { ticks: { callback: (v) => 'R$ ' + v.toLocaleString('pt-BR') } }
    }
  }
});
```

Exibir abaixo do gráfico:

- Card "Melhor mês": nome do mês + valor em verde
- Card "Pior mês": nome do mês + valor em vermelho
- Select de filtro por ano (submete form via GET)

---

## FECHAMENTO DE CAIXA — RELATÓRIO

```
Fechamento de Caixa — 05/06/2025
Caixa responsável: [Todos ▾]   [Filtrar]
───────────────────────────────────────────────────
  Total vendido:          R$ 3.200,00
  Vendas finalizadas:     18
  Vendas estornadas:      2
  ─────────────────────────────────────────────────
  Dinheiro:               R$ 1.200,00
  Pix:                    R$ 1.500,00
  Cartão:                 R$ 500,00
  ─────────────────────────────────────────────────
  Valor líquido:          R$ 3.200,00
───────────────────────────────────────────────────
[ Imprimir ]   [ Exportar CSV ]
```

- Tabela responsiva com `table-bordered`
- Botão "Imprimir" usa `window.print()` com CSS de impressão (`@media print`)
- Botão "Exportar CSV" aciona view Django que retorna `HttpResponse` com `Content-Type: text/csv`
- Filtros de data e caixa via GET, renderizados acima do relatório

---

## LISTAGENS (PADRÃO GERAL)

Todas as telas de listagem devem seguir este padrão:

```
[Título da seção]          [+ Novo]

Filtros:  [Campo ▾]  [Busca ____]  [Filtrar]

┌──────────────────────────────────────────────────┐
│  Col1       Col2       Col3       Ações          │
├──────────────────────────────────────────────────┤
│  Dado1      Dado2      Dado3      [✏] [⊘]        │
│  ...        ...        ...        ...            │
└──────────────────────────────────────────────────┘

  < 1  2  3  4  5 >     Exibindo 1-20 de 87
```

Regras:

- Usar `table-responsive` para scroll horizontal em mobile
- Paginação via `django.core.paginator.Paginator` (padrão 20 itens/página)
- Componente de paginação em `components/pagination.html`
- Botão "Novo" alinhado à direita do título com ícone `bi-plus-lg`
- Ações na última coluna: editar (`bi-pencil`) e desativar (`bi-toggle-on/off`) — nunca deletar hard
- Linha de produto com estoque crítico: destacar com classe `table-danger` ou badge vermelho na coluna de estoque

---

## FORMULÁRIOS (PADRÃO GERAL)

Todos os formulários devem seguir este padrão:

```
[Título]
────────────────────────────────

  Nome completo *
  [____________________________]

  Email
  [____________________________]

  Perfil *
  [Selecionar ▾]

────────────────────────────────
[ Salvar ]   [ Cancelar ]
```

Regras:

- Labels acima dos campos (nunca placeholder como substituto de label)
- Campos obrigatórios marcados com asterisco vermelho `*`
- Validação Bootstrap: classes `is-valid` / `is-invalid` após submit
- Mensagem de erro inline abaixo do campo: `<div class="invalid-feedback">`
- Botões no rodapé: "Salvar" (`btn-primary`) e "Cancelar" (`btn-outline-secondary`)
- Formulários complexos em `card` com `card-body`

---

## PRIMEIRO ACESSO — TROCA DE SENHA

Template dedicado `accounts/primeiro_acesso.html` (herda `base_auth.html`):

```
┌───────────────────────────────────────┐
│  Bem-vindo, João Silva!               │
│                                       │
│  Este é seu primeiro acesso.          │
│  Defina sua senha pessoal.            │
│                                       │
│  Nova senha *                         │
│  [____________________________]       │
│                                       │
│  Confirmar senha *                    │
│  [____________________________]       │
│                                       │
│  [ Definir senha e entrar ]           │
└───────────────────────────────────────┘
```

- Meter de força da senha com JavaScript simples (fraco/médio/forte)
- Botão toggle mostrar/ocultar senha (`bi-eye` / `bi-eye-slash`)
- Redirecionar para dashboard após sucesso

---

## BADGE DE STATUS (PADRÃO)

Criar tag de template customizada `{% status_badge status %}`:

| Status       | Classe Bootstrap     | Ícone                       |
|--------------|----------------------|-----------------------------|
| `ABERTA`     | `badge bg-warning`   | `bi-hourglass-split`        |
| `FINALIZADA` | `badge bg-success`   | `bi-check-circle`           |
| `ESTORNADA`  | `badge bg-danger`    | `bi-arrow-counterclockwise` |
| `ATIVO`      | `badge bg-success`   | `bi-check`                  |
| `INATIVO`    | `badge bg-secondary` | `bi-dash-circle`            |
| `ENTRADA`    | `badge bg-info`      | `bi-arrow-down-circle`      |
| `VENDA`      | `badge bg-primary`   | `bi-cart-check`             |
| `ESTORNO`    | `badge bg-danger`    | `bi-arrow-counterclockwise` |
| `AJUSTE`     | `badge bg-warning`   | `bi-tools`                  |

---

## RESPONSIVIDADE

Breakpoints obrigatórios:

- **Desktop (≥992px):** sidebar fixa, layout duas colunas onde aplicável
- **Tablet (768–991px):** sidebar recolhida por padrão, toggle manual
- **Mobile (<768px):** sidebar como offcanvas Bootstrap, tabelas com scroll horizontal, cards empilhados

Testar todas as telas nos três breakpoints antes de entregar.

---

## ACESSIBILIDADE MÍNIMA

- Todo `<img>` com `alt`
- Todos os ícones decorativos com `aria-hidden="true"`
- Botões de ação com `aria-label` descritivo
- Campos de formulário com `for` vinculado ao `id` do input
- Contraste mínimo WCAG AA nas cores da identidade visual

---

## ARQUIVO `gestok.js`

Centralizar toda lógica JavaScript customizada:

```javascript
// gestok.js

// 1. Calcular subtotal e total na tela de nova venda
// 2. Preencher preço ao selecionar produto (fetch /api/products/{id}/)
// 3. Adicionar/remover linhas do formset dinamicamente
// 4. Exibir meter de força de senha
// 5. Toggle mostrar/ocultar senha
// 6. Auto-dismiss de alerts após 5s
// 7. Confirmar ações destrutivas (estorno, desativação)
```

---

# MÓDULO DE USUÁRIOS

O sistema deve possuir gerenciamento próprio de usuários. Não depender exclusivamente do Django Admin. Apenas o perfil **ADMINISTRADOR** pode cadastrar usuários.

**Menu:** Usuários → Listar Usuários / Cadastrar Usuário / Usuários Inativos

---

## PERFIS

### ADMINISTRADOR

Pode:

- Cadastrar, editar, ativar e desativar usuários
- Cadastrar e editar produtos
- Alterar preços
- Visualizar e estornar vendas
- Acessar relatórios e dashboard completo

### VENDAS

Pode:

- Visualizar produtos e estoque
- Criar vendas abertas

Não pode:

- Finalizar vendas
- Alterar preços
- Estornar vendas
- Acessar relatórios

### CAIXA

Pode:

- Visualizar vendas abertas
- Acessar tela de caixa
- Finalizar vendas
- Registrar pagamentos
- Consultar produtos e estoque
- Visualizar suas próprias vendas finalizadas

Não pode:

- Alterar preços
- Cadastrar produtos
- Estornar vendas
- Acessar relatórios administrativos

---

## CADASTRO DE USUÁRIOS

Campos: nome completo, telefone, email, endereço, cargo (organizacional), perfil.

**Cargo** — apenas organizacional, não controla permissões. Exemplos:

```
Operador de Caixa
Atendente de Vendas
Estoquista
Supervisor
Gerente Comercial
Gerente Geral
```

**Matrícula:** gerada automaticamente pelo sistema, sequencial a partir de 1000 (1000, 1001, 1002…), única, imutável e indexada. Utilizada como login no sistema. O administrador não informa a matrícula.

**Senha temporária padrão:** todo usuário novo recebe a senha `senha123` no cadastro. O campo `primeiro_acesso` é definido como `True` e o sistema obriga a troca da senha no primeiro login, bloqueando o acesso ao restante da aplicação até que ela seja alterada.

---

# PRODUTOS

## CÓDIGO DO PRODUTO

Gerado automaticamente. Formato: `GST-000001`, `GST-000002`, …

## MODEL `Category`

Campos: `nome`, `descricao`, `ativo`

## MODEL `Product`

Campos: `codigo_produto`, `nome`, `descricao`, `categoria`, `preco_custo`, `preco_venda`, `estoque_atual`, `estoque_minimo`, `ativo`, `criado_em`, `atualizado_em`

## ALERTA DE ESTOQUE BAIXO

Crítico quando `estoque_atual <= estoque_minimo`. Exibir badge vermelho e destacar no dashboard do administrador e na topbar.

## MODEL `InventoryMovement`

Campos: `codigo_movimentacao` (MOV-000001), `produto`, `tipo` (ENTRADA/VENDA/ESTORNO/AJUSTE), `quantidade`, `estoque_anterior`, `estoque_posterior`, `usuario`, `observacao`, `criado_em`.

Toda alteração de estoque deve gerar uma movimentação registrada.

---

# VENDAS

## MODEL `Sale`

Campos: `numero_venda` (VEN-000001), `vendedor`, `caixa_responsavel`, `data_venda`, `data_finalizacao`, `forma_pagamento`, `valor_total`, `status` (ABERTA/FINALIZADA/ESTORNADA), `estornada`

## MODEL `SaleItem`

Campos: `venda`, `produto`, `quantidade`, `preco_unitario`, `subtotal`

## FLUXO DE VENDA

```
Perfil Vendas cria venda
↓
Adiciona produtos
↓
Sistema calcula total
↓
Venda fica ABERTA
↓
Aparece para o Caixa
↓
Caixa seleciona venda
↓
Registra pagamento
↓
Sistema valida estoque
↓
Sistema baixa estoque
↓
Sistema finaliza venda
```

## REGRAS

- Bloquear: venda sem itens; quantidade ≤ 0; produto inativo; estoque insuficiente
- Usar `transaction.atomic()` na finalização

---

# ESTORNOS

Somente **ADMINISTRADOR**. Validar venda finalizada, impedir duplicata, devolver estoque, gerar movimentação ESTORNO, registrar responsável. Código: `EST-000001`.

---

# API REST

A API é de uso interno do sistema, consumida pelo `gestok.js` para busca de preços e dados de produtos. Não há menu de acesso à API no sistema web.

```
GET    /api/products/
POST   /api/products/
GET    /api/products/{id}/
PUT    /api/products/{id}/
PATCH  /api/products/{id}/
DELETE /api/products/{id}/

GET    /api/categories/
POST   /api/categories/
GET    /api/categories/{id}/
PUT    /api/categories/{id}/
PATCH  /api/categories/{id}/
DELETE /api/categories/{id}/
```

Permissões: usuários autenticados podem consultar; apenas o perfil **ADMINISTRADOR** pode criar, editar e remover. Documentação técnica disponível em `/api/schema/` e `/api/docs/` (acesso restrito, não exibido na sidebar).

API deve ter suporte para um possivel integração futura com outras aplicações como react e mobile

---



# AUDITORIA

Registrar: login, logout, criação/alteração de usuário, alteração de preço, venda criada/finalizada, estorno, ajuste de estoque.

Campos: `usuario`, `matricula`, `acao`, `data`, `hora`, `ip`

---

# DADOS INICIAIS

```bash
python manage.py seed_data
```

Criar:

- Grupos: Administrador, Caixa, Vendas
- Usuários: `admin` / `caixa` / `vendas` com senha `senha123` e `primeiro_acesso = True`
- Categorias de exemplo
- Produtos de exemplo
- Movimentações iniciais

---

# TESTES

Validar:

- Login por matrícula
- Criação de usuário
- Geração automática de matrícula
- Troca obrigatória de senha no primeiro acesso
- Alerta de estoque baixo
- Criação de venda
- Finalização de venda
- Baixa de estoque
- Estorno
- Controle de permissões por perfil
- Endpoints da API

---

# DOCUMENTAÇÃO FINAL

Criar `RESUMO_DO_PROJETO.md` com:

- Visão geral
- Arquitetura
- Apps e suas responsabilidades
- Models utilizados
- Fluxo de vendas
- Fluxo de estoque
- Fluxo de caixa
- Permissões por perfil
- API
- Relatórios
- Instruções completas de execução
