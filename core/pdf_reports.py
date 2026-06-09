from html import escape
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from cashier.services import cash_register_summary


NAVY = colors.HexColor('#0B1B2F')
BLUE = colors.HexColor('#4F8CFF')
LIGHT_BLUE = colors.HexColor('#DCE8FA')
MUTED = colors.HexColor('#5C6F88')
GREEN = colors.HexColor('#008A5A')
RED = colors.HexColor('#C9364F')
GRID = colors.HexColor('#CCD6E3')


def money(value):
    value = value or 0
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def local_datetime(value):
    if not value:
        return '-'
    return timezone.localtime(value).strftime('%d/%m/%Y %H:%M')


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=NAVY,
        spaceAfter=5 * mm,
    ))
    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=MUTED,
        spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=NAVY,
        spaceBefore=3 * mm,
        spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name='Cell',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name='CellRight',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=TA_RIGHT,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name='Empty',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=MUTED,
        spaceBefore=10 * mm,
    ))
    return styles


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GRID)
    canvas.line(doc.leftMargin, 12 * mm, doc.pagesize[0] - doc.rightMargin, 12 * mm)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 7 * mm, 'Gestok - Sistema de Vendas')
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        7 * mm,
        f'Página {doc.page}',
    )
    canvas.restoreState()


def _table(data, widths, alignments=None):
    table = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.35, GRID),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F8FC')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]
    for column, alignment in (alignments or {}).items():
        style.append(('ALIGN', (column, 1), (column, -1), alignment))
    table.setStyle(TableStyle(style))
    return table


def build_cash_closing_pdf(cash_registers, generated_by, period_label):
    registers = list(cash_registers)
    buffer = BytesIO()
    styles = _styles()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title='Relatório de Fechamento de Caixa',
        author='Gestok',
    )
    story = [
        Paragraph('Relatório de Fechamento de Caixa', styles['ReportTitle']),
        Paragraph(
            f"Período: {escape(period_label)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Emitido por: {escape(generated_by)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Emissão: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}",
            styles['ReportSubtitle'],
        ),
    ]

    if not registers:
        story.append(Paragraph('Nenhum fechamento encontrado para os filtros informados.', styles['Empty']))

    for index, cash_register in enumerate(registers):
        summary = cash_register_summary(cash_register)
        expected = cash_register.valor_esperado
        if expected is None:
            expected = summary['expected_cash']
        difference = cash_register.diferenca_fechamento
        if difference is None and cash_register.valor_fechamento is not None:
            difference = cash_register.valor_fechamento - expected

        if index:
            story.append(PageBreak())

        story.append(Paragraph(
            f"Caixa #{cash_register.id} - {escape(cash_register.operador.nome_completo)}",
            styles['SectionTitle'],
        ))
        register_data = [
            ['Abertura', 'Fechamento', 'Status', 'Vendas'],
            [
                local_datetime(cash_register.data_abertura),
                local_datetime(cash_register.data_fechamento),
                cash_register.get_status_display(),
                str(summary['sales_count']),
            ],
        ]
        story.append(_table(register_data, [42 * mm, 42 * mm, 28 * mm, 28 * mm]))
        story.append(Spacer(1, 3 * mm))

        financial_data = [
            ['Abertura', 'Dinheiro', 'Pix', 'Cartão', 'Outros', 'Total vendido'],
            [
                money(cash_register.valor_abertura),
                money(summary['total_dinheiro']),
                money(summary['total_pix']),
                money(summary['total_cartao']),
                money(summary['total_outros']),
                money(summary['total_sales']),
            ],
        ]
        story.append(_table(
            financial_data,
            [28 * mm, 28 * mm, 25 * mm, 28 * mm, 25 * mm, 32 * mm],
            {0: 'RIGHT', 1: 'RIGHT', 2: 'RIGHT', 3: 'RIGHT', 4: 'RIGHT', 5: 'RIGHT'},
        ))
        story.append(Spacer(1, 3 * mm))

        closing_data = [
            ['Esperado em dinheiro', 'Valor declarado', 'Diferença'],
            [
                money(expected),
                money(cash_register.valor_fechamento),
                money(difference),
            ],
        ]
        closing_table = _table(
            closing_data,
            [52 * mm, 52 * mm, 52 * mm],
            {0: 'RIGHT', 1: 'RIGHT', 2: 'RIGHT'},
        )
        if difference is not None:
            closing_table.setStyle(TableStyle([
                ('TEXTCOLOR', (2, 1), (2, 1), GREEN if difference == 0 else RED),
                ('FONTNAME', (2, 1), (2, 1), 'Helvetica-Bold'),
            ]))
        story.append(closing_table)

        if cash_register.observacao_fechamento:
            story.extend([
                Paragraph('Observação', styles['SectionTitle']),
                Paragraph(escape(cash_register.observacao_fechamento), styles['Cell']),
            ])

        story.append(Paragraph('Vendas do Caixa', styles['SectionTitle']))
        sales_rows = [['Venda', 'Finalização', 'Vendedor', 'Pagamento', 'Valor']]
        for sale in summary['finalized_sales']:
            sales_rows.append([
                Paragraph(escape(sale.numero_venda), styles['Cell']),
                Paragraph(local_datetime(sale.data_finalizacao), styles['Cell']),
                Paragraph(escape(sale.vendedor.nome_completo), styles['Cell']),
                Paragraph(escape(sale.get_forma_pagamento_display()), styles['Cell']),
                Paragraph(money(sale.valor_total), styles['CellRight']),
            ])
        if len(sales_rows) == 1:
            sales_rows.append(['-', '-', 'Nenhuma venda finalizada', '-', money(0)])
        story.append(_table(
            sales_rows,
            [25 * mm, 34 * mm, 45 * mm, 28 * mm, 28 * mm],
            {4: 'RIGHT'},
        ))

    document.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()


def build_movements_pdf(movements, generated_by, filters):
    movement_list = list(movements)
    buffer = BytesIO()
    styles = _styles()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=18 * mm,
        title='Relatório de Movimentações de Estoque',
        author='Gestok',
    )
    filter_text = ' | '.join(
        f"{label}: {escape(value)}"
        for label, value in filters
        if value
    ) or 'Sem filtros'
    story = [
        Paragraph('Relatório de Movimentações de Estoque', styles['ReportTitle']),
        Paragraph(
            f"{filter_text}<br/>Emitido por: {escape(generated_by)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Emissão: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}",
            styles['ReportSubtitle'],
        ),
    ]

    rows = [[
        'Código', 'Data/Hora', 'Produto', 'Tipo', 'Qtd.', 'Anterior',
        'Posterior', 'Usuário', 'Observação',
    ]]
    totals = {}
    net_quantity = 0
    for movement in movement_list:
        totals[movement.tipo] = totals.get(movement.tipo, 0) + abs(movement.quantidade)
        delta = movement.estoque_posterior - movement.estoque_anterior
        net_quantity += delta
        rows.append([
            Paragraph(escape(movement.codigo_movimentacao), styles['Cell']),
            Paragraph(local_datetime(movement.criado_em), styles['Cell']),
            Paragraph(
                f"{escape(movement.produto.nome)}<br/>"
                f"<font color='#5C6F88'>{escape(movement.produto.codigo_produto)}</font>",
                styles['Cell'],
            ),
            Paragraph(escape(movement.get_tipo_display()), styles['Cell']),
            Paragraph(str(movement.quantidade), styles['CellRight']),
            Paragraph(str(movement.estoque_anterior), styles['CellRight']),
            Paragraph(str(movement.estoque_posterior), styles['CellRight']),
            Paragraph(escape(movement.usuario.nome_completo), styles['Cell']),
            Paragraph(escape(movement.observacao or '-'), styles['Cell']),
        ])
    if len(rows) == 1:
        rows.append(['-', '-', 'Nenhuma movimentação encontrada', '-', '-', '-', '-', '-', '-'])

    story.append(_table(
        rows,
        [25 * mm, 30 * mm, 45 * mm, 23 * mm, 15 * mm, 18 * mm, 18 * mm, 37 * mm, 55 * mm],
        {4: 'RIGHT', 5: 'RIGHT', 6: 'RIGHT'},
    ))
    story.append(Spacer(1, 5 * mm))

    total_parts = [
        f"Registros: {len(movement_list)}",
        f"Saldo líquido: {net_quantity:+d}",
    ]
    for key, label in (
        ('ENTRADA', 'Entradas'),
        ('VENDA', 'Vendas'),
        ('ESTORNO', 'Estornos'),
        ('AJUSTE', 'Ajustes'),
    ):
        total_parts.append(f"{label}: {totals.get(key, 0)}")
    story.append(Paragraph(' &nbsp;&nbsp;|&nbsp;&nbsp; '.join(total_parts), styles['ReportSubtitle']))

    document.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()


def build_sales_pdf(sales, generated_by, filters):
    sale_list = list(sales)
    buffer = BytesIO()
    styles = _styles()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=18 * mm,
        title='Relatório de Vendas',
        author='Gestok',
    )
    filter_text = ' | '.join(
        f"{label}: {escape(value)}"
        for label, value in filters
        if value
    ) or 'Sem filtros'
    story = [
        Paragraph('Relatório de Vendas', styles['ReportTitle']),
        Paragraph(
            f"{filter_text}<br/>Emitido por: {escape(generated_by)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Emissão: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}",
            styles['ReportSubtitle'],
        ),
    ]

    rows = [[
        'Venda', 'Abertura', 'Finalização', 'Vendedor', 'Pagamento',
        'Itens', 'Status', 'Valor',
    ]]
    status_totals = {}
    payment_totals = {}
    total_value = 0
    for sale in sale_list:
        status_totals[sale.status] = status_totals.get(sale.status, 0) + 1
        if sale.status == 'FINALIZADA':
            total_value += sale.valor_total
            payment_key = sale.forma_pagamento or 'PENDENTE'
            payment_totals[payment_key] = (
                payment_totals.get(payment_key, 0) + sale.valor_total
            )
        rows.append([
            Paragraph(escape(sale.numero_venda), styles['Cell']),
            Paragraph(local_datetime(sale.data_venda), styles['Cell']),
            Paragraph(local_datetime(sale.data_finalizacao), styles['Cell']),
            Paragraph(escape(sale.vendedor.nome_completo), styles['Cell']),
            Paragraph(
                escape(sale.get_forma_pagamento_display())
                if sale.forma_pagamento else 'Pendente',
                styles['Cell'],
            ),
            Paragraph(str(getattr(sale, 'item_count', 0)), styles['CellRight']),
            Paragraph(escape(sale.get_status_display()), styles['Cell']),
            Paragraph(money(sale.valor_total), styles['CellRight']),
        ])
    if len(rows) == 1:
        rows.append(['-', '-', '-', 'Nenhuma venda encontrada', '-', '-', '-', money(0)])

    story.append(_table(
        rows,
        [25 * mm, 31 * mm, 31 * mm, 48 * mm, 31 * mm, 16 * mm, 27 * mm, 29 * mm],
        {5: 'RIGHT', 7: 'RIGHT'},
    ))
    story.append(Spacer(1, 5 * mm))

    status_labels = {
        'ABERTA': 'Abertas',
        'FINALIZADA': 'Finalizadas',
        'ESTORNADA': 'Estornadas',
    }
    payment_labels = {
        'DINHEIRO': 'Dinheiro',
        'PIX': 'Pix',
        'CARTAO': 'Cartão',
        'OUTROS': 'Outros',
    }
    summary_parts = [
        f"Registros: {len(sale_list)}",
        f"Total finalizado: {money(total_value)}",
    ]
    summary_parts.extend(
        f"{status_labels[key]}: {status_totals.get(key, 0)}"
        for key in status_labels
    )
    story.append(Paragraph(
        ' &nbsp;&nbsp;|&nbsp;&nbsp; '.join(summary_parts),
        styles['ReportSubtitle'],
    ))

    if payment_totals:
        payment_summary = ' &nbsp;&nbsp;|&nbsp;&nbsp; '.join(
            f"{payment_labels.get(key, key.title())}: {money(value)}"
            for key, value in payment_totals.items()
        )
        story.append(Paragraph(
            f"Formas de pagamento: {payment_summary}",
            styles['ReportSubtitle'],
        ))

    document.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
