from flask import Flask, render_template, request, redirect, send_file
from datetime import date, datetime
from models import db, Operator, DailyRecord, Setting
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///retain.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def dashboard():

    operators = Operator.query.filter_by(
        active=True
    ).order_by(
        Operator.name
    ).all()

    records = DailyRecord.query.order_by(
        DailyRecord.date.asc()
    ).all()

    setting = Setting.query.first()

    if not setting:
        setting = Setting(
            retention_target=85.0
        )

        db.session.add(setting)
        db.session.commit()

    today = date.today()

    # DATA SELECIONADA NO FILTRO DO DASHBOARD
    selected_date_raw = request.args.get(
        "data",
        today.isoformat()
    )

    try:
        selected_date = date.fromisoformat(
            selected_date_raw
        )
    except ValueError:
        selected_date = today

    # RESULTADO DO DIA SELECIONADO
    today_records = [
        record
        for record in records
        if record.date == selected_date
    ]


    total_calls = sum(
        record.calls_handled
        for record in today_records
    )

    total_cancellations = sum(
        record.cancellations
        for record in today_records
    )

    total_retentions = sum(
        record.retentions
        for record in today_records
    )

    if total_calls > 0:
        retention_percentage = (
            total_retentions / total_calls
        ) * 100
    else:
        retention_percentage = 0

    # =========================
    # EQUIPES
    # =========================
    teams = {}

    for team_name in ["Manhã", "Tarde"]:

        team_records = [
            record
            for record in today_records
            if record.operator.team == team_name
        ]

        calls = sum(
            record.calls_handled
            for record in team_records
        )

        cancellations = sum(
            record.cancellations
            for record in team_records
        )

        retentions = sum(
            record.retentions
            for record in team_records
        )

        if calls > 0:
            percentage = (
                retentions / calls
            ) * 100
        else:
            percentage = 0

        teams[team_name] = {
            "calls": calls,
            "cancellations": cancellations,
            "retentions": retentions,
            "percentage": percentage
        }

    # =========================
    # DESEMPENHO DOS OPERADORES
    # =========================
    operator_results = []

    for operator in operators:

        operator_records = [
            record
            for record in today_records
            if record.operator_id == operator.id
        ]

        calls = sum(
            record.calls_handled
            for record in operator_records
        )

        cancellations = sum(
            record.cancellations
            for record in operator_records
        )

        retentions = sum(
            record.retentions
            for record in operator_records
        )

        if calls > 0:
            percentage = (
                retentions / calls
            ) * 100
        else:
            percentage = 0

        operator_results.append({
            "name": operator.name,
            "team": operator.team,
            "calls": calls,
            "cancellations": cancellations,
            "retentions": retentions,
            "percentage": percentage
        })


    operator_results.sort(
        key=lambda item: item["percentage"],
        reverse=True
    )

    # =========================
    # EVOLUÇÃO POR DIA
    # =========================
    evolution = []

    dates = sorted(
        set(record.date for record in records),
        reverse=True
    )

    for record_date in dates:

        day_records = [
            record
            for record in records
            if record.date == record_date
        ]

        calls = sum(
            record.calls_handled
            for record in day_records
        )

        retentions = sum(
            record.retentions
            for record in day_records
        )

        if calls > 0:
            percentage = (
                retentions / calls
            ) * 100
        else:
            percentage = 0

        evolution.append({
            "date": record_date,
            "percentage": percentage,
            "calls": calls
        })
    # DADOS PARA O GRÁFICO DE EVOLUÇÃO
    chart_dates = [
        item["date"].strftime("%d/%m")
        for item in reversed(evolution)
    ]

    chart_percentages = [
        round(item["percentage"], 1)
        for item in reversed(evolution)
    ]

    chart_targets = [
        setting.retention_target
        for item in reversed(evolution)
    ]

    return render_template(
        "dashboard.html",
        operators=operators,
        total_operators=len(operators),
        total_calls=total_calls,
        total_cancellations=total_cancellations,
        total_retentions=total_retentions,
        retention_percentage=retention_percentage,
        retention_target=setting.retention_target,
        teams=teams,
        operator_results=operator_results,
        evolution=evolution,
        today=selected_date,
        chart_dates=chart_dates,
        chart_percentages=chart_percentages,
        chart_targets=chart_targets
    )


@app.route("/operators")
def operators():
    operators = Operator.query.filter_by(active=True).order_by(Operator.name).all()

    return render_template(
        "operators.html",
        operators=operators
    )

@app.route("/records")
def records():
    records = DailyRecord.query.order_by(
        DailyRecord.date.desc()
    ).all()

    return render_template(
        "records.html",
        records=records
    )


@app.route("/reports")
def reports():
    today = date.today()

    # Datas padrão: primeiro dia do mês até hoje
    default_start = today.replace(day=1)
    default_end = today

    start_raw = request.args.get(
        "data_inicio",
        default_start.isoformat()
    )
    end_raw = request.args.get(
        "data_fim",
        default_end.isoformat()
    )

    try:
        start_date = date.fromisoformat(start_raw)
        end_date = date.fromisoformat(end_raw)
    except ValueError:
        start_date = default_start
        end_date = default_end

    # Corrige período invertido
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Busca os lançamentos do período
    records = DailyRecord.query.filter(
        DailyRecord.date >= start_date,
        DailyRecord.date <= end_date
    ).order_by(
        DailyRecord.date.desc()
    ).all()

    # Indicadores consolidados
    total_calls = sum(
        record.calls_handled for record in records
    )

    total_cancellations = sum(
        record.cancellations for record in records
    )

    total_retentions = sum(
        record.retentions for record in records
    )

    if total_calls > 0:
        retention_percentage = (
            total_retentions / total_calls
        ) * 100
    else:
        retention_percentage = 0

    # RESULTADOS POR EQUIPE NO PERÍODO
    team_results = {}

    for team_name in ["Manhã", "Tarde"]:
        team_records = [
            record
            for record in records
            if record.operator.team == team_name
        ]

        calls = sum(
            record.calls_handled
            for record in team_records
        )

        cancellations = sum(
            record.cancellations
            for record in team_records
        )

        retentions = sum(
            record.retentions
            for record in team_records
        )

        if calls > 0:
            percentage = (retentions / calls) * 100
        else:
            percentage = 0

        team_results[team_name] = {
            "calls": calls,
            "cancellations": cancellations,
            "retentions": retentions,
            "percentage": percentage
        }
    # DESEMPENHO INDIVIDUAL NO PERÍODO
    operator_results = []

    all_operators = Operator.query.order_by(
        Operator.name
    ).all()

    for operator in all_operators:
        operator_records = [
            record
            for record in records
            if record.operator_id == operator.id
        ]

        calls = sum(
            record.calls_handled
            for record in operator_records
        )

        cancellations = sum(
            record.cancellations
            for record in operator_records
        )

        retentions = sum(
            record.retentions
            for record in operator_records
        )

        if calls > 0:
            percentage = (retentions / calls) * 100
        else:
            percentage = 0

        operator_results.append({
            "id": operator.id,
            "name": operator.name,
            "team": operator.team,
            "active": operator.active,
            "calls": calls,
            "cancellations": cancellations,
            "retentions": retentions,
            "percentage": percentage
        })

    operator_results.sort(
        key=lambda item: item["percentage"],
        reverse=True
    )


    # Meta configurada
    setting = Setting.query.first()

    if not setting:
        setting = Setting(retention_target=85.0)
        db.session.add(setting)
        db.session.commit()

    return render_template(
        "reports.html",
        records=records,
        retention_target=setting.retention_target,
        start_date=start_date,
        end_date=end_date,
        total_calls=total_calls,
        total_cancellations=total_cancellations,
        total_retentions=total_retentions,
        retention_percentage=retention_percentage,
        team_results=team_results,
        operator_results=operator_results
    )
@app.route("/operators/<int:operator_id>", methods=["GET", "POST"])
def operator_detail(operator_id):
    operator = Operator.query.get_or_404(operator_id)
    records = DailyRecord.query.filter_by(
        operator_id=operator.id
    ).order_by(DailyRecord.date.desc()).all()

    setting = Setting.query.first()
    if not setting:
        setting = Setting(retention_target=85.0)
        db.session.add(setting)
        db.session.commit()

    if request.method == "POST":
        record_date = date.fromisoformat(request.form["date"])

        existing_record = DailyRecord.query.filter_by(
            operator_id=operator.id,
            date=record_date
        ).first()

        if existing_record:
            return "Já existe um lançamento para este operador nesta data."

        calls_handled = int(request.form["calls"])
        cancellations = int(request.form["cancellations"])
        if cancellations > calls_handled:
            return "O número de cancelamentos não pode ser maior que o número de ligações atendidas."

        retentions = calls_handled - cancellations

        record = DailyRecord(
            operator_id=operator.id,
            date=record_date,
            calls_handled=calls_handled,
            cancellations=cancellations,
            retentions=retentions
        )

        db.session.add(record)
        db.session.commit()

        return redirect(f"/operators/{operator.id}")

    return render_template(
        "operator_detail.html",
        operator=operator,
        today=date.today().isoformat(),
        records=records,
        retention_target=setting.retention_target
    )

@app.route("/operators/<int:operator_id>/record/<int:record_id>/edit", methods=["GET", "POST"])
def edit_record(operator_id, record_id):
    operator = Operator.query.get_or_404(operator_id)

    record = DailyRecord.query.filter_by(
        id=record_id,
        operator_id=operator_id
    ).first_or_404()

    if request.method == "POST":
        record.date = date.fromisoformat(request.form["date"])

        calls_handled = int(request.form["calls"])
        cancellations = int(request.form["cancellations"])

        if cancellations > calls_handled:
            return "O número de cancelamentos não pode ser maior que o número de ligações atendidas."

        record.calls_handled = calls_handled
        record.cancellations = cancellations

        # Retenção calculada automaticamente
        record.retentions = calls_handled - cancellations

        db.session.commit()

        return redirect(f"/operators/{operator.id}")

    return render_template(
        "edit_record.html",
        operator=operator,
        record=record
    )

@app.route("/settings", methods=["GET", "POST"])
def settings():
    setting = Setting.query.first()

    if not setting:
        setting = Setting(retention_target=85.0)
        db.session.add(setting)
        db.session.commit()

    if request.method == "POST":
        setting.retention_target = float(
            request.form["retention_target"]
        )

        db.session.commit()

        return redirect("/settings")

    return render_template(
        "settings.html",
        setting=setting
    )

@app.route("/operators/new", methods=["GET", "POST"])
def new_operator():
    if request.method == "POST":
        name = request.form["name"]
        team = request.form["team"]

        operator = Operator(
            name=name,
            team=team
        )

        db.session.add(operator)
        db.session.commit()

        return redirect("/operators")

    return render_template("new_operator.html")

@app.route("/operators/<int:operator_id>/edit", methods=["GET", "POST"])
def edit_operator(operator_id):
    operator = Operator.query.get_or_404(operator_id)

    if request.method == "POST":
        operator.name = request.form["name"]
        operator.team = request.form["team"]
        operator.active = request.form["active"] == "true"

        db.session.commit()

        return redirect(f"/operators/{operator.id}")

    return render_template(
        "edit_operator.html",
        operator=operator
    )

@app.route("/reports/pdf")
def export_report_pdf():
    today = date.today()

    default_start = today.replace(day=1)
    default_end = today

    start_raw = request.args.get(
        "data_inicio",
        default_start.isoformat()
    )
    end_raw = request.args.get(
        "data_fim",
        default_end.isoformat()
    )

    try:
        start_date = date.fromisoformat(start_raw)
        end_date = date.fromisoformat(end_raw)
    except ValueError:
        start_date = default_start
        end_date = default_end

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    records = DailyRecord.query.filter(
        DailyRecord.date >= start_date,
        DailyRecord.date <= end_date
    ).order_by(
        DailyRecord.date.desc()
    ).all()

    setting = Setting.query.first()
    retention_target = (
        setting.retention_target if setting else 85.0
    )

    # INDICADORES GERAIS
    total_calls = sum(r.calls_handled for r in records)
    total_cancellations = sum(r.cancellations for r in records)
    total_retentions = sum(r.retentions for r in records)

    retention_percentage = (
        total_retentions / total_calls * 100
        if total_calls > 0 else 0
    )

    # RESULTADOS POR EQUIPE
    team_results = []

    for team_name in ["Manhã", "Tarde"]:
        team_records = [
            r for r in records
            if r.operator.team == team_name
        ]

        calls = sum(r.calls_handled for r in team_records)
        cancellations = sum(r.cancellations for r in team_records)
        retentions = sum(r.retentions for r in team_records)
        percentage = (
            retentions / calls * 100 if calls > 0 else 0
        )

        team_results.append([
            team_name,
            calls,
            cancellations,
            retentions,
            f"{percentage:.1f}%",
            "Atingida" if calls > 0 and percentage >= retention_target
            else ("Abaixo da meta" if calls > 0 else "Sem dados")
        ])

    # RESULTADOS POR OPERADOR
    operators = Operator.query.order_by(Operator.name).all()
    operator_results = []

    for operator in operators:
        operator_records = [
            r for r in records
            if r.operator_id == operator.id
        ]

        calls = sum(r.calls_handled for r in operator_records)
        cancellations = sum(r.cancellations for r in operator_records)
        retentions = sum(r.retentions for r in operator_records)
        percentage = (
            retentions / calls * 100 if calls > 0 else 0
        )

        operator_results.append({
            "name": operator.name,
            "team": operator.team,
            "active": operator.active,
            "calls": calls,
            "cancellations": cancellations,
            "retentions": retentions,
            "percentage": percentage,
            "has_data": calls > 0
        })

    operator_results.sort(
        key=lambda item: (
            not item["has_data"],
            -item["percentage"],
            item["name"].lower()
        )
    )

    # DOCUMENTO PDF
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title="Relatório Retain",
        author="Retain - Gestão de Retenção"
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="RetainTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=28,
        textColor=colors.HexColor("#10a37f"),
        alignment=TA_LEFT,
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        name="RetainSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#555566"),
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        name="RetainSection",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#202123"),
        spaceBefore=12,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="RetainSmall",
        parent=styles["Normal"],
        fontSize=8,
        leading=10
    ))

    story = []

    story.append(Paragraph("RETAIN", styles["RetainTitle"]))
    story.append(Paragraph(
        "Relatório de Gestão de Retenção",
        styles["Heading2"]
    ))
    story.append(Paragraph(
        f"Período: {start_date.strftime('%d/%m/%Y')} a "
        f"{end_date.strftime('%d/%m/%Y')}<br/>"
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}<br/>"
        f"Meta de retenção: {retention_target:.1f}%",
        styles["RetainSubtitle"]
    ))

    # CARDS RESUMIDOS
    story.append(Paragraph(
        "Resumo consolidado",
        styles["RetainSection"]
    ))

    summary_data = [[
        "Ligações atendidas",
        "Cancelamentos",
        "Retenções",
        "Retenção geral"
    ], [
        str(total_calls),
        str(total_cancellations),
        str(total_retentions),
        f"{retention_percentage:.1f}%"
    ]]

    summary_table = Table(
        summary_data,
        colWidths=[65 * mm, 65 * mm, 65 * mm, 65 * mm],
        rowHeights=[10 * mm, 15 * mm]
    )

    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#202123")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#edf7f3")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#202123")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5dd")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5dd")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 5 * mm))

    status = (
        "Meta atingida"
        if total_calls > 0 and retention_percentage >= retention_target
        else ("Abaixo da meta" if total_calls > 0 else "Sem dados")
    )

    story.append(Paragraph(
        f"Resultado geral: <b>{status}</b>",
        styles["Normal"]
    ))

    # COMPARATIVO ENTRE EQUIPES
    story.append(Paragraph(
        "Comparativo entre equipes",
        styles["RetainSection"]
    ))

    team_data = [[
        "Equipe",
        "Ligações",
        "Cancelamentos",
        "Retenções",
        "Retenção",
        "Situação da meta"
    ]] + team_results

    team_table = Table(
        team_data,
        colWidths=[35 * mm, 35 * mm, 40 * mm, 35 * mm, 35 * mm, 55 * mm],
        repeatRows=1
    )

    team_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#202123")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5dd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white, colors.HexColor("#f2f4f7")
        ]),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
    ]))

    story.append(team_table)

    # DESEMPENHO INDIVIDUAL
    story.append(PageBreak())
    story.append(Paragraph(
        "Desempenho por operador",
        styles["RetainSection"]
    ))
    story.append(Paragraph(
        "Resultados individuais no período selecionado.",
        styles["RetainSubtitle"]
    ))

    operator_data = [[
        "Operador",
        "Equipe",
        "Status",
        "Ligações",
        "Cancelamentos",
        "Retenções",
        "Retenção",
        "Meta"
    ]]

    for operator in operator_results:
        if not operator["has_data"]:
            target_status = "Sem dados"
        elif operator["percentage"] >= retention_target:
            target_status = "Atingida"
        else:
            target_status = "Abaixo da meta"

        operator_data.append([
            Paragraph(operator["name"], styles["RetainSmall"]),
            operator["team"],
            "Ativo" if operator["active"] else "Inativo",
            str(operator["calls"]),
            str(operator["cancellations"]),
            str(operator["retentions"]),
            f"{operator['percentage']:.1f}%",
            target_status
        ])

    operator_table = Table(
        operator_data,
        colWidths=[
            48 * mm, 23 * mm, 23 * mm, 25 * mm,
            30 * mm, 25 * mm, 25 * mm, 35 * mm
        ],
        repeatRows=1
    )

    operator_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#202123")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d5dd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white, colors.HexColor("#f2f4f7")
        ]),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
    ]))

    story.append(operator_table)

    def draw_page(canvas, doc):
        canvas.saveState()
        page_width, page_height = landscape(A4)

        canvas.setStrokeColor(colors.HexColor("#10a37f"))
        canvas.setLineWidth(1.2)
        canvas.line(
            15 * mm,
            13 * mm,
            page_width - 15 * mm,
            13 * mm
        )

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666677"))
        canvas.drawString(
            15 * mm,
            8 * mm,
            "Retain® | Gestão de Retenção | Desenvolvido por Allyson Matheus Ribeiro | Contato: ribeiro.amrs@gmail.com"
        )
        canvas.drawRightString(
            page_width - 15 * mm,
            8 * mm,
            f"Página {doc.page}"
        )

        canvas.restoreState()

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page
    )

    buffer.seek(0)

    filename = (
        f"retain_relatorio_{start_date.isoformat()}_"
        f"{end_date.isoformat()}.pdf"
    )

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    app.run(debug=True)