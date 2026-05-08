"""
backend/relatorio.py
Gera relatórios em PDF para o sistema de CMV.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from datetime import datetime
from db import get_connection, is_postgres
from sql_compat import q

def gerar_pdf_semanal(output_path="relatorio_semanal.pdf"):
    """Gera um PDF consolidado dos KPIs e CMV da semana."""
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Título
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, textColor=colors.HexColor("#f59e0b"))
    elements.append(Paragraph("Relatório Semanal de CMV - Quintal Goiano", title_style))
    elements.append(Spacer(1, 12))
    
    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Gerado em: {data_geracao}", styles['Normal']))
    elements.append(Spacer(1, 24))

    conn = get_connection()
    try:
        # 1. KPIs Gerais
        row = conn.execute(q("""
            SELECT 
                SUM(receita_total_plat) as receita,
                SUM(pedidos) as pedidos,
                AVG(ticket_medio) as ticket
            FROM vendas
        """)).fetchone()
        
        kpi_data = [
            ["Faturamento (Plataformas)", f"R$ {(row['receita'] or 0):.2f}"],
            ["Total de Pedidos", f"{row['pedidos'] or 0}"],
            ["Ticket Médio", f"R$ {(row['ticket'] or 0):.2f}"]
        ]
        
        t_kpis = Table(kpi_data, colWidths=[200, 150])
        t_kpis.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(Paragraph("Resumo Operacional", styles['Heading2']))
        elements.append(t_kpis)
        elements.append(Spacer(1, 24))

        # 2. Insumos Críticos (Estoque Baixo)
        elements.append(Paragraph("Insumos com Estoque Crítico", styles['Heading2']))
        insumos = conn.execute(q("""
            SELECT nome, estoque_atual, estoque_minimo, unidade
            FROM insumos
            WHERE estoque_atual <= estoque_minimo AND estoque_minimo > 0
            LIMIT 10
        """)).fetchall()
        
        if insumos:
            ins_data = [["Insumo", "Atual", "Mínimo"]]
            for i in insumos:
                ins_data.append([i["nome"], f"{i['estoque_atual']} {i['unidade']}", f"{i['estoque_minimo']} {i['unidade']}"])
            
            t_ins = Table(ins_data, colWidths=[200, 75, 75])
            t_ins.setStyle(TableStyle([
                ('TEXTCOLOR', (1, 1), (1, -1), colors.red),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#fef3c7")),
            ]))
            elements.append(t_ins)
        else:
            elements.append(Paragraph("Nenhum insumo abaixo do estoque mínimo.", styles['Normal']))
            
        elements.append(Spacer(1, 24))

        # 3. Desperdício
        elements.append(Paragraph("Desperdício da Semana", styles['Heading2']))
        perdas = conn.execute(q("""
            SELECT COALESCE(i.nome, pr.nome) as item, SUM(p.quantidade) as qtd, SUM(p.custo_estimado) as custo
            FROM perdas p
            LEFT JOIN insumos i ON p.insumo_id = i.id
            LEFT JOIN pratos pr ON p.prato_id = pr.id
            GROUP BY item
            ORDER BY custo DESC
        """)).fetchall()

        if perdas:
            p_data = [["Item", "Qtd", "Custo Estimado"]]
            total_p = 0
            for p in perdas:
                p_data.append([p["item"], f"{p['qtd']}", f"R$ {p['custo']:.2f}"])
                total_p += p['custo']
            p_data.append(["TOTAL", "", f"R$ {total_p:.2f}"])
            
            t_p = Table(p_data, colWidths=[200, 50, 100])
            t_p.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(t_p)
        else:
            elements.append(Paragraph("Nenhuma perda registrada.", styles['Normal']))

    finally:
        conn.close()

    doc.build(elements)
    return output_path

if __name__ == "__main__":
    path = gerar_pdf_semanal("relatorio_teste.pdf")
    print(f"Relatório gerado em: {path}")
