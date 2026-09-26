import marimo


app = marimo.App(width="full", app_title="iGOT Lab Workspace")


@app.cell
def __():
    import marimo as mo
    return (mo,)


@app.cell
def __(mo):
    mo.md(
        """
        # iGOT isolated lab workspace

        This disposable workspace is attached only to the targets assigned to
        the current lab session. Files under `/workspace` are removed when the
        session is reset or terminated unless an artifact is explicitly saved.
        """
    )
    return


if __name__ == "__main__":
    app.run()
