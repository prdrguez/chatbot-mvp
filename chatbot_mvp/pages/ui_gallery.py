import reflex as rx

from chatbot_mvp.components.layout import layout


def _demo_chip(label: str) -> rx.Component:
    return rx.box(
        rx.text(label, size="2"),
        padding="0.35rem 0.6rem",
        border_radius="0.5rem",
        background_color="var(--gray-3)",
        border="1px solid var(--gray-6)",
    )


def _section(title: str, content: rx.Component, description: str = "") -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            rx.cond(
                description != "",
                rx.text(description, color="var(--gray-600)"),
                rx.box(),
            ),
            content,
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _grid_example() -> rx.Component:
    grid = getattr(rx, "grid", None)
    if grid is None:
        return rx.text("Grid no disponible", color="var(--gray-600)")
    return grid(
        _demo_chip("G1"),
        _demo_chip("G2"),
        _demo_chip("G3"),
        columns="3",
        gap="2",
        width="100%",
    )


def _simple_grid_example() -> rx.Component:
    simple_grid = getattr(rx, "simple_grid", None)
    if simple_grid is None:
        return rx.text("SimpleGrid no disponible", color="var(--gray-600)")
    return simple_grid(
        _demo_chip("S1"),
        _demo_chip("S2"),
        _demo_chip("S3"),
        columns=3,
        spacing="2",
        width="100%",
    )


def _callout_example() -> rx.Component:
    callout = getattr(rx, "callout", None)
    if callout is None:
        return rx.text("Callout no disponible", color="var(--gray-600)")
    if hasattr(callout, "root"):
        icon = getattr(rx, "icon", None)
        if icon is None:
            return rx.text("Icon no disponible", color="var(--gray-600)")
        return callout.root(
            callout.icon(icon(tag="info")),
            callout.text("Ejemplo de callout informativo."),
        )
    return rx.text("Callout no disponible", color="var(--gray-600)")


def _select_example() -> rx.Component:
    select = getattr(rx, "select", None)
    if select is None:
        return rx.text("Select no disponible", color="var(--gray-600)")
    if hasattr(select, "root"):
        return select.root(
            select.trigger(placeholder="Elige una opcion"),
            select.content(
                select.item("Opcion A", value="a"),
                select.item("Opcion B", value="b"),
                select.item("Opcion C", value="c"),
            ),
            width="220px",
        )
    return rx.text("Select no disponible", color="var(--gray-600)")


def _text_area_example() -> rx.Component:
    text_area = getattr(rx, "text_area", None)
    if text_area is None:
        return rx.text("Textarea no disponible", color="var(--gray-600)")
    return text_area(placeholder="Textarea basica", width="100%")


def _slider_example() -> rx.Component:
    slider = getattr(rx, "slider", None)
    if slider is None:
        return rx.text("Slider no disponible", color="var(--gray-600)")
    if hasattr(slider, "root"):
        return slider.root(
            slider.track(slider.range()),
            slider.thumb(),
            default_value=[40],
            width="220px",
        )
    return slider(default_value=[40], width="220px")


def _checkbox_example() -> rx.Component:
    checkbox = getattr(rx, "checkbox", None)
    if checkbox is None:
        return rx.text("Checkbox no disponible", color="var(--gray-600)")
    return checkbox("Checkbox", is_checked=True)


def _switch_example() -> rx.Component:
    switch = getattr(rx, "switch", None)
    if switch is None:
        return rx.text("Switch no disponible", color="var(--gray-600)")
    return switch(is_checked=True)


def _tabs_example() -> rx.Component:
    tabs = getattr(rx, "tabs", None)
    if tabs is None or not hasattr(tabs, "root"):
        return rx.text("Tabs no disponible", color="var(--gray-600)")
    return tabs.root(
        tabs.list(
            tabs.trigger("Resumen", value="resumen"),
            tabs.trigger("Detalle", value="detalle"),
        ),
        tabs.content(
            rx.text("Contenido de resumen."),
            value="resumen",
        ),
        tabs.content(
            rx.text("Contenido de detalle."),
            value="detalle",
        ),
        default_value="resumen",
        width="100%",
    )


def _progress_example() -> rx.Component:
    progress = getattr(rx, "progress", None)
    if progress is None:
        return rx.text("Progress no disponible", color="var(--gray-600)")
    return progress(value=65, width="220px")


def _spinner_example() -> rx.Component:
    spinner = getattr(rx, "spinner", None)
    if spinner is None:
        return rx.text("Spinner no disponible", color="var(--gray-600)")
    return spinner(size="3")


def _skeleton_example() -> rx.Component:
    skeleton = getattr(rx, "skeleton", None)
    if skeleton is None:
        return rx.text("Skeleton no disponible", color="var(--gray-600)")
    return skeleton(height="1.5rem", width="220px")


def _separator_example() -> rx.Component:
    separator = getattr(rx, "separator", None)
    if separator is None:
        return rx.text("Separator no disponible", color="var(--gray-600)")
    return separator()


def _table_example() -> rx.Component:
    table = getattr(rx, "table", None)
    if table is None or not hasattr(table, "root"):
        return rx.text("Table no disponible", color="var(--gray-600)")
    return table.root(
        table.header(
            table.row(
                table.column_header_cell("Componente"),
                table.column_header_cell("Uso"),
            )
        ),
        table.body(
            table.row(
                table.cell("Card"),
                table.cell("Contenedor de contenido"),
            ),
            table.row(
                table.cell("Badge"),
                table.cell("Etiqueta compacta"),
            ),
        ),
        width="100%",
    )


def ui_gallery() -> rx.Component:
    return layout(
        rx.container(
            rx.vstack(
                rx.heading("UI Gallery (Demo)", size="7"),
                rx.text(
                    "Catalogo rapido de componentes Reflex/Radix disponibles.",
                    color="var(--gray-600)",
                ),
                _section(
                    "Layout",
                    rx.vstack(
                        rx.text("Container", font_weight="600"),
                        rx.container(
                            rx.hstack(
                                _demo_chip("A"),
                                _demo_chip("B"),
                                _demo_chip("C"),
                                spacing="2",
                            ),
                            width="100%",
                        ),
                        rx.text("Flex / HStack / VStack", font_weight="600"),
                        rx.flex(
                            _demo_chip("Flex 1"),
                            _demo_chip("Flex 2"),
                            _demo_chip("Flex 3"),
                            gap="2",
                            wrap="wrap",
                        ),
                        rx.hstack(
                            _demo_chip("H1"),
                            _demo_chip("H2"),
                            _demo_chip("H3"),
                            spacing="2",
                        ),
                        rx.vstack(
                            _demo_chip("V1"),
                            _demo_chip("V2"),
                            spacing="2",
                            align="start",
                        ),
                        rx.text("Grid / SimpleGrid", font_weight="600"),
                        _grid_example(),
                        _simple_grid_example(),
                        spacing="2",
                        align="start",
                        width="100%",
                    ),
                ),
                _section(
                    "Superficies",
                    rx.vstack(
                        rx.card(rx.text("Ejemplo de card"), width="100%"),
                        _callout_example(),
                        rx.hstack(
                            rx.badge("Nuevo", variant="soft"),
                            rx.badge("Activo", color_scheme="green"),
                            spacing="2",
                        ),
                        _separator_example(),
                        spacing="2",
                        align="start",
                        width="100%",
                    ),
                ),
                _section(
                    "Inputs",
                    rx.vstack(
                        rx.input(placeholder="Input basico", width="100%"),
                        _text_area_example(),
                        _select_example(),
                        _slider_example(),
                        rx.hstack(
                            rx.hstack(
                                _switch_example(),
                                rx.text("Switch"),
                                spacing="2",
                                align="center",
                            ),
                            _checkbox_example(),
                            rx.radio_group.root(
                                rx.hstack(
                                    rx.radio_group.item(
                                        "Radio A",
                                        value="a",
                                    ),
                                    rx.radio_group.item(
                                        "Radio B",
                                        value="b",
                                    ),
                                    spacing="3",
                                ),
                                value="a",
                            ),
                            spacing="4",
                            align="center",
                            wrap="wrap",
                        ),
                        spacing="3",
                        align="start",
                        width="100%",
                    ),
                ),
                _section(
                    "Navegacion",
                    _tabs_example(),
                ),
                _section(
                    "Feedback",
                    rx.hstack(
                        _progress_example(),
                        _spinner_example(),
                        _skeleton_example(),
                        spacing="4",
                        align="center",
                        wrap="wrap",
                    ),
                ),
                _section("Tabla", _table_example()),
                spacing="5",
                align="start",
                width="100%",
            ),
            width="100%",
            max_width="900px",
        )
    )
