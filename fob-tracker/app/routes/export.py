from datetime import date

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from .. import auth, export_xlsx

bp = Blueprint("export", __name__)


@bp.route("/export", methods=["GET"])
@auth.require_admin
def export_view():
    today = date.today()
    return render_template(
        "export.html",
        default_month=f"{today.year:04d}-{today.month:02d}",
    )


@bp.route("/export/download", methods=["GET"])
@auth.require_admin
def download():
    month_str = request.args.get("month", "")
    try:
        year_s, mon_s = month_str.split("-")
        year, month = int(year_s), int(mon_s)
        if not (1 <= month <= 12):
            raise ValueError
    except ValueError:
        flash("Pick a month in YYYY-MM form.", "err")
        return redirect(url_for("export.export_view"))

    data = export_xlsx.build_monthly_workbook(year, month)
    filename = f"fob-report-{year:04d}-{month:02d}.xlsx"
    return Response(
        data,
        mimetype=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
