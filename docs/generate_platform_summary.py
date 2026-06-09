from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs' / 'Gestok_Resumo_Plataforma.pdf'
LOGO = ROOT / 'static' / 'img' / 'logo.png'

NAVY = colors.HexColor('#07182B')
SURFACE = colors.HexColor('#102A46')
BLUE = colors.HexColor('#4F8CFF')
LIGHT_BLUE = colors.HexColor('#E8F1FF')
CYAN = colors.HexColor('#69B7FF')
GREEN = colors.HexColor('#008F63')
RED = colors.HexColor('#CF4058')
GOLD = colors.HexColor('#D88B00')
TEXT = colors.HexColor('#16263A')
MUTED = colors.HexColor('#61748B')
LINE = colors.HexColor('#D7E0EB')
SOFT = colors.HexColor('#F4F7FB')
WHITE = colors.white


def register_fonts():
    regular = Path('C:/Windows/Fonts/arial.ttf')
    bold = Path('C:/Windows/Fonts/arialbd.ttf')
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont('GestokSans', str(regular)))
        pdfmetrics.registerFont(TTFont('GestokSans-Bold', str(bold)))
        return 'GestokSans', 'GestokSans-Bold'
    return 'Helvetica', 'Helvetica-Bold'


FONT, FONT_BOLD = register_fonts()


def styles():
    base = getSampleStyleSheet()
    return {
        'cover_brand': ParagraphStyle(
            'cover_brand',
            parent=base['Normal'],
            fontName=FONT_BOLD,
            fontSize=13,
            leading=16,
            textColor=CYAN,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        ),
        'cover_title': ParagraphStyle(
            'cover_title',
            parent=base['Title'],
            fontName=FONT_BOLD,
            fontSize=29,
            leading=34,
            textColor=WHITE,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        ),
        'cover_subtitle': ParagraphStyle(
            'cover_subtitle',
            parent=base['Normal'],
            fontName=FONT,
            fontSize=12,
            leading=18,
            textColor=colors.HexColor('#C7D8EE'),
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        ),
        'h1': ParagraphStyle(
            'h1',
            parent=base['Heading1'],
            fontName=FONT_BOLD,
            fontSize=18,
            leading=23,
            textColor=NAVY,
            spaceBefore=2 * mm,
            spaceAfter=4 * mm,
            keepWithNext=True,
        ),
        'h2': ParagraphStyle(
            'h2',
            parent=base['Heading2'],
            fontName=FONT_BOLD,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#244E80'),
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        ),
        'body': ParagraphStyle(
            'body',
            parent=base['BodyText'],
            fontName=FONT,
            fontSize=9,
            leading=13,
            textColor=TEXT,
            spaceAfter=2.5 * mm,
        ),
        'small': ParagraphStyle(
            'small',
            parent=base['BodyText'],
            fontName=FONT,
            fontSize=7.4,
            leading=10,
            textColor=TEXT,
        ),
        'small_bold': ParagraphStyle(
            'small_bold',
            parent=base['BodyText'],
            fontName=FONT_BOLD,
            fontSize=7.4,
            leading=10,
            textColor=TEXT,
        ),
        'table_header': ParagraphStyle(
            'table_header',
            parent=base['BodyText'],
            fontName=FONT_BOLD,
            fontSize=7.4,
            leading=10,
            textColor=WHITE,
        ),
        'bullet': ParagraphStyle(
            'bullet',
            parent=base['BodyText'],
            fontName=FONT,
            fontSize=8.7,
            leading=12,
            leftIndent=5 * mm,
            firstLineIndent=-3 * mm,
            bulletIndent=1.5 * mm,
            textColor=TEXT,
            spaceAfter=1.2 * mm,
        ),
        'step_number': ParagraphStyle(
            'step_number',
            parent=base['Normal'],
            fontName=FONT_BOLD,
            fontSize=14,
            leading=18,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        'step_title': ParagraphStyle(
            'step_title',
            parent=base['BodyText'],
            fontName=FONT_BOLD,
            fontSize=8.8,
            leading=11,
            textColor=NAVY,
            spaceAfter=1 * mm,
        ),
        'step_body': ParagraphStyle(
            'step_body',
            parent=base['BodyText'],
            fontName=FONT,
            fontSize=7.8,
            leading=10.5,
            textColor=MUTED,
        ),
        'callout': ParagraphStyle(
            'callout',
            parent=base['BodyText'],
            fontName=FONT,
            fontSize=8.5,
            leading=12,
            textColor=TEXT,
        ),
        'route': ParagraphStyle(
            'route',
            parent=base['BodyText'],
            fontName=FONT_BOLD,
            fontSize=7,
            leading=9,
            textColor=colors.HexColor('#244E80'),
        ),
    }


S = styles()


def p(text, style='body'):
    return Paragraph(text, S[style])


def bullet(text):
    return Paragraph(f'• {text}', S['bullet'])


def section(title):
    return [Spacer(1, 2 * mm), p(title, 'h1')]


def table(data, widths, header=True, alignments=None, font_size=7.4):
    prepared = []
    for row_index, row in enumerate(data):
        prepared_row = []
        for cell in row:
            if isinstance(cell, Paragraph):
                prepared_row.append(cell)
            else:
                prepared_row.append(p(str(cell), 'table_header' if header and row_index == 0 else 'small'))
        prepared.append(prepared_row)

    result = LongTable(prepared, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
    style = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.35, LINE),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SOFT]),
    ]
    if header:
        style.extend([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), font_size),
        ])
    for column, alignment in (alignments or {}).items():
        style.append(('ALIGN', (column, 1 if header else 0), (column, -1), alignment))
    result.setStyle(TableStyle(style))
    return result


def callout(title, text, accent=BLUE):
    content = Table(
        [[
            '',
            p(f'<b>{title}</b><br/>{text}', 'callout'),
        ]],
        colWidths=[3 * mm, 159 * mm],
        hAlign='LEFT',
    )
    content.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('BACKGROUND', (0, 0), (0, 0), accent),
        ('BOX', (0, 0), (-1, -1), 0.5, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 7),
        ('RIGHTPADDING', (1, 0), (1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return content


def step_row(number, title, description):
    badge = Table([[p(str(number), 'step_number')]], colWidths=[11 * mm], rowHeights=[11 * mm])
    badge.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 0, BLUE),
    ]))
    return [
        badge,
        [p(title, 'step_title'), p(description, 'step_body')],
    ]


def steps(items):
    data = [step_row(index, title, description) for index, (title, description) in enumerate(items, 1)]
    result = Table(data, colWidths=[14 * mm, 148 * mm], hAlign='LEFT')
    result.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (1, 0), (1, -2), 0.35, LINE),
    ]))
    return result


def first_page(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)
    canvas.setFillColor(BLUE)
    canvas.rect(0, height - 7 * mm, width, 7 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor('#0D2845'))
    canvas.circle(width - 5 * mm, 12 * mm, 48 * mm, stroke=0, fill=1)
    canvas.restoreState()


def later_pages(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 12 * mm, width, 12 * mm, stroke=0, fill=1)
    canvas.setFont(FONT_BOLD, 8)
    canvas.setFillColor(WHITE)
    canvas.drawString(16 * mm, height - 8 * mm, 'GESTOK')
    canvas.setFont(FONT, 7)
    canvas.setFillColor(colors.HexColor('#C7D8EE'))
    canvas.drawRightString(width - 16 * mm, height - 8 * mm, 'Guia da Plataforma')
    canvas.setStrokeColor(LINE)
    canvas.line(16 * mm, 13 * mm, width - 16 * mm, 13 * mm)
    canvas.setFont(FONT, 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(16 * mm, 8 * mm, 'Gestok - Sistema de vendas, estoque e caixa')
    canvas.drawRightString(width - 16 * mm, 8 * mm, f'Página {doc.page}')
    canvas.restoreState()


def build_story():
    story = []

    story.extend([
        Spacer(1, 31 * mm),
        Image(str(LOGO), width=38 * mm, height=38 * mm),
        Spacer(1, 10 * mm),
        p('GESTOK', 'cover_brand'),
        p('Resumo da Plataforma', 'cover_title'),
        p(
            'Sistema integrado de vendas, estoque, usuários e operação de caixa '
            'para mercados e pequenos comércios.',
            'cover_subtitle',
        ),
        Spacer(1, 16 * mm),
        p('Arquitetura • Módulos • Permissões • Rotas • Fluxo de uso', 'cover_subtitle'),
        Spacer(1, 36 * mm),
        p('Documentação da versão atual • Junho de 2026', 'cover_subtitle'),
        PageBreak(),
    ])

    story += section('1. Visão geral')
    story.append(p(
        'O Gestok centraliza a rotina operacional de um comércio em uma única '
        'aplicação web. O sistema acompanha o produto desde o cadastro e a '
        'entrada no estoque até a venda no PDV, a baixa automática, a auditoria '
        'da movimentação e o fechamento financeiro do caixa.'
    ))
    story.append(callout(
        'Objetivo da plataforma',
        'Reduzir controles paralelos e manter vendas, estoque, operadores e '
        'caixas conectados por uma trilha de dados consistente.',
    ))
    story.append(Spacer(1, 4 * mm))

    feature_data = [
        ['Módulo', 'O que entrega'],
        ['Dashboard', 'Indicadores críticos de vendas e estoque para o gerente.'],
        ['Vendas', 'Histórico, filtros, detalhes, estornos e exportação em PDF.'],
        ['Produtos', 'Catálogo, categorias, preços, estoque mínimo e status.'],
        ['Movimentações', 'Auditoria de entradas, vendas, estornos e ajustes.'],
        ['Caixa / PDV', 'Abertura diária, venda rápida, pagamentos e fechamento.'],
        ['Usuários', 'Cadastro, edição, cargos, primeiro acesso e perfil.'],
        ['Relatórios', 'PDFs de vendas, movimentações e fechamento de caixa.'],
        ['API', 'Consulta e administração autenticada de categorias e produtos.'],
    ]
    story.append(table(feature_data, [35 * mm, 127 * mm]))

    story += section('2. Stack e arquitetura')
    stack_data = [
        ['Camada', 'Tecnologia', 'Responsabilidade'],
        ['Backend', 'Python + Django 5', 'Regras de negócio, autenticação, ORM e páginas.'],
        ['Banco', 'MySQL / MariaDB', 'Persistência transacional em utf8mb4.'],
        ['Frontend', 'Templates + Bootstrap 5', 'Interface responsiva no tema escuro.'],
        ['Interação', 'JavaScript', 'Painéis laterais, filtros e ações do PDV.'],
        ['Gráficos', 'Chart.js', 'Visualizações do dashboard gerencial.'],
        ['API', 'Django REST Framework', 'Endpoints autenticados de catálogo.'],
        ['PDF', 'ReportLab', 'Relatórios reproduzíveis no servidor.'],
    ]
    story.append(table(stack_data, [29 * mm, 44 * mm, 89 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(p(
        '<b>Organização:</b> cada domínio possui models, views, URLs, formulários, '
        'templates e testes próprios. O Django ORM conecta os módulos ao banco, '
        'enquanto mixins de autorização protegem as telas no backend.'
    ))

    story.append(PageBreak())
    story += section('3. Permissões por cargo')
    story.append(p(
        'O acesso é definido pelo cargo operacional. O perfil interno é derivado '
        'automaticamente e não aparece como uma escolha separada no cadastro.'
    ))
    permission_data = [
        ['Recurso', 'Gerente', 'Atendente', 'Estoquista'],
        ['Dashboard', 'Sim', 'Não', 'Não'],
        ['Vendas', 'Todas', 'Próprias', 'Não'],
        ['Caixa / PDV', 'Sim', 'Sim', 'Não'],
        ['Fechamentos', 'Todos', 'Próprios', 'Não'],
        ['Movimentações', 'Sim', 'Sim', 'Não'],
        ['Produtos', 'Administra', 'Não', 'Consulta'],
        ['Ajuste de estoque', 'Sim', 'Não', 'Não'],
        ['Estorno de venda', 'Sim', 'Não', 'Não'],
        ['Usuários', 'Administra', 'Não', 'Não'],
        ['Perfil próprio', 'Sim', 'Sim', 'Sim'],
    ]
    permissions = table(
        permission_data,
        [62 * mm, 34 * mm, 34 * mm, 32 * mm],
        alignments={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'},
    )
    permissions.setStyle(TableStyle([
        ('TEXTCOLOR', (1, 1), (-1, -1), TEXT),
        ('FONTNAME', (1, 1), (-1, -1), FONT_BOLD),
    ]))
    story.append(permissions)
    story.append(Spacer(1, 3 * mm))
    story.append(callout(
        'Defesa em profundidade',
        'O menu mostra somente os módulos permitidos, mas as views também '
        'validam o cargo. Digitar uma rota manualmente não contorna a permissão.',
        accent=GREEN,
    ))

    story += section('4. Fluxo operacional')
    story.append(p('Preparação do ambiente:'))
    story.append(steps([
        ('Cadastros básicos', 'O gerente cria categorias, produtos, preços e estoque inicial.'),
        ('Equipe', 'O gerente cadastra usuários e atribui Gerente, Atendente ou Estoquista.'),
        ('Primeiro acesso', 'O usuário entra com matrícula e senha temporária e define uma nova senha.'),
    ]))
    story.append(Spacer(1, 4 * mm))
    story.append(p('Rotina diária do caixa:'))
    story.append(steps([
        ('Abertura', 'O primeiro acesso ao PDV no dia exige o valor inicial de troco.'),
        ('Venda', 'O operador pesquisa produtos, ajusta quantidades e escolhe o pagamento.'),
        ('Estoque', 'A finalização baixa o saldo e cria movimentações auditáveis por produto.'),
        ('Fechamento', 'O operador informa o valor contado; o sistema calcula esperado e diferença.'),
        ('Consulta posterior', 'O histórico permite exportar o caixa individual ou o período filtrado.'),
    ]))
    story.append(Spacer(1, 4 * mm))
    story.append(callout(
        'Proteção diária',
        'Um caixa aberto em dia anterior bloqueia novas vendas até ser conferido '
        'e finalizado. O sistema também evita duplicidade de abertura por operador.',
        accent=GOLD,
    ))

    story += section('5. Vendas, estoque e auditoria')
    story.append(p(
        'Uma venda começa com status <b>ABERTA</b>. Seus itens recalculam o total '
        'automaticamente. Ao finalizar, o estoque de cada produto é validado e '
        'reduzido dentro de uma transação; cada baixa gera uma movimentação do '
        'tipo <b>VENDA</b>. Um estorno administrativo devolve o estoque e registra '
        'uma movimentação do tipo <b>ESTORNO</b>.'
    ))
    audit_data = [
        ['Evento', 'Efeito no estoque', 'Registro de auditoria'],
        ['Entrada', 'Aumenta', 'Produto, quantidade, antes/depois, usuário e observação.'],
        ['Venda', 'Diminui', 'Ligada à venda e ao operador responsável.'],
        ['Estorno', 'Aumenta', 'Registra a devolução e o motivo informado.'],
        ['Ajuste', 'Conforme operação', 'Mantém o saldo anterior e posterior.'],
    ]
    story.append(table(audit_data, [31 * mm, 35 * mm, 96 * mm]))
    story.append(Spacer(1, 3 * mm))
    story.append(p(
        '<b>Identificadores:</b> produtos usam <b>GST-000001</b>, movimentações '
        '<b>MOV-000001</b>, vendas <b>VEN-000001</b> e usuários recebem matrícula '
        'numérica sequencial.'
    ))

    story += section('6. Modelo de dados')
    model_data = [
        ['Modelo', 'Papel no sistema', 'Relações importantes'],
        ['CustomUser', 'Identidade, cargo e estado do acesso.', 'Vendas, caixas e movimentações.'],
        ['Category', 'Organização do catálogo.', 'Possui produtos.'],
        ['Product', 'Preço, categoria e saldos de estoque.', 'Itens de venda e movimentações.'],
        ['InventoryMovement', 'Trilha de toda alteração de estoque.', 'Produto e usuário responsável.'],
        ['Sale', 'Cabeçalho financeiro e operacional.', 'Vendedor, caixa e itens.'],
        ['SaleItem', 'Produto, quantidade, preço e subtotal.', 'Venda e produto.'],
        ['CashRegister', 'Sessão diária de operação do caixa.', 'Operador e vendas relacionadas.'],
    ]
    story.append(table(model_data, [34 * mm, 64 * mm, 64 * mm]))
    story.append(Spacer(1, 3 * mm))
    story.append(p(
        'Relacionamentos históricos usam proteção contra exclusão quando a '
        'remoção quebraria a auditoria. Produtos e usuários podem ser inativados '
        'sem desaparecer dos registros anteriores.'
    ))

    story += section('7. Relatórios e exportações')
    report_data = [
        ['Relatório', 'Filtros', 'Conteúdo principal'],
        ['Vendas', 'Busca, status e período', 'Vendas, valores, pagamentos, status e resumo.'],
        ['Movimentações', 'Busca, tipo, produto e período', 'Quantidade, estoque antes/depois, usuário e observação.'],
        ['Fechamento', 'Operador e período', 'Abertura, pagamentos, esperado, declarado, diferença e vendas.'],
    ]
    story.append(table(report_data, [34 * mm, 52 * mm, 76 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(p(
        'Os PDFs são criados no servidor com ReportLab e respeitam os mesmos '
        'filtros e limites de acesso das telas. O gerente pode consolidar a '
        'operação; o atendente exporta somente seus próprios dados financeiros.'
    ))

    story += section('8. Rotas principais')
    routes = [
        ['Módulo', 'Rota', 'Finalidade'],
        ['Acesso', '/accounts/login/', 'Login por matrícula.'],
        ['Acesso', '/accounts/primeiro-acesso/', 'Definição obrigatória da primeira senha.'],
        ['Perfil', '/accounts/profile/', 'Informações do usuário atual.'],
        ['Usuários', '/accounts/users/', 'Lista e administração de usuários.'],
        ['Produtos', '/products/', 'Catálogo e filtros de produtos.'],
        ['Produtos', '/products/new/', 'Cadastro de produto.'],
        ['Estoque', '/products/movements/', 'Histórico de movimentações.'],
        ['Estoque', '/products/movements/pdf/', 'PDF das movimentações filtradas.'],
        ['Vendas', '/sales/my-sales/', 'Histórico de vendas.'],
        ['Vendas', '/sales/my-sales/pdf/', 'PDF das vendas filtradas.'],
        ['Vendas', '/sales/&lt;id&gt;/', 'Detalhes da venda.'],
        ['Caixa', '/cashier/', 'Ponto de venda.'],
        ['Caixa', '/cashier/abrir/', 'Abertura diária.'],
        ['Caixa', '/cashier/fechar/', 'Fechamento e conferência.'],
        ['Caixa', '/cashier/fechamentos/', 'Histórico de fechamentos.'],
        ['Relatórios', '/reports/dashboard/', 'Dashboard gerencial.'],
        ['Relatórios', '/reports/fechamento-caixa/pdf/', 'PDF de fechamento.'],
        ['API', '/api/categories/', 'API de categorias.'],
        ['API', '/api/products/', 'API de produtos.'],
    ]
    route_table = table(routes, [27 * mm, 61 * mm, 74 * mm])
    for row in range(1, len(routes)):
        route_table._cellvalues[row][1] = p(routes[row][1], 'route')
    story.append(route_table)

    story.append(PageBreak())
    story += section('9. Segurança, testes e produção')
    story.append(p(
        'A aplicação utiliza sessão do Django, proteção CSRF, senhas com hash, '
        'middleware de primeiro acesso e autorização por mixins. Operações de '
        'estoque, venda e fechamento usam transações nos pontos críticos.'
    ))
    for item in [
        'A suíte automatizada cobre login, primeiro acesso, cargos e isolamento de dados.',
        'Também são testados abertura/fechamento, filtros e geração válida dos PDFs.',
        'A API exige autenticação; gravações são reservadas ao perfil administrativo.',
    ]:
        story.append(bullet(item))
    story.append(Spacer(1, 3 * mm))
    story.append(callout(
        'Antes de publicar',
        'Mover SECRET_KEY e credenciais do banco para variáveis de ambiente, '
        'desativar DEBUG, restringir ALLOWED_HOSTS, configurar HTTPS, backups, '
        'servidor WSGI e uma senha temporária aleatória.',
        accent=RED,
    ))

    story += section('10. Como executar')
    commands = [
        ['Etapa', 'Comando'],
        ['Instalar dependências', 'python -m pip install -r requirements.txt'],
        ['Aplicar banco', 'python manage.py migrate'],
        ['Criar gerente', 'python manage.py createsuperuser'],
        ['Executar testes', 'python manage.py test'],
        ['Iniciar sistema', 'python manage.py runserver'],
    ]
    story.append(table(commands, [49 * mm, 113 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(p(
        'A configuração atual utiliza MySQL/MariaDB, banco <b>gestok_db</b> e '
        'fuso <b>America/Manaus</b>. Consulte o README do repositório para as '
        'instruções completas de instalação e manutenção.'
    ))

    return story


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=24 * mm,
        leftMargin=24 * mm,
        topMargin=20 * mm,
        bottomMargin=19 * mm,
        title='Gestok - Resumo da Plataforma',
        author='Gestok',
        subject='Arquitetura, módulos, permissões, rotas e fluxo de uso',
    )
    document.build(build_story(), onFirstPage=first_page, onLaterPages=later_pages)
    print(OUTPUT)


if __name__ == '__main__':
    main()
