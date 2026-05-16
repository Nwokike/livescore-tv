import flet as ft


class AppColors:
    PRIMARY = "#10B981"  # Emerald 500 (football green)
    SECONDARY = "#3B82F6"  # Blue 500
    SUCCESS = "#22C55E"  # Green 500
    WARNING = "#F59E0B"  # Amber 500
    ERROR = "#EF4444"  # Red 500
    LIVE = "#EF4444"  # Red for live indicator

    # Dark Mode
    DARK_BG = "#0B0F19"
    DARK_SURFACE = "#111827"
    DARK_SURFACE_VARIANT = "#1F2937"
    DARK_TEXT = "#F9FAFB"
    DARK_TEXT_DIM = "#9CA3AF"
    DARK_TEXT_MUTED = "#6B7280"

    # Light Mode
    LIGHT_BG = "#F8FAFC"
    LIGHT_SURFACE = "#FFFFFF"
    LIGHT_SURFACE_VARIANT = "#F1F5F9"
    LIGHT_TEXT = "#0F172A"
    LIGHT_TEXT_DIM = "#64748B"
    LIGHT_TEXT_MUTED = "#94A3B8"

    SPLASH_BG = "#0B0F19"

    WHITE = ft.Colors.WHITE
    BLACK = ft.Colors.BLACK
    TRANSPARENT = ft.Colors.TRANSPARENT

    @staticmethod
    def get_glass_bg(page: ft.Page):
        return ft.Colors.with_opacity(
            0.05, ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK
        )

    @staticmethod
    def get_hover_bg(page: ft.Page):
        return ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK
        )

    @staticmethod
    def get_surface_variant(page: ft.Page):
        return AppColors.DARK_SURFACE_VARIANT if page.theme_mode == ft.ThemeMode.DARK else AppColors.LIGHT_SURFACE_VARIANT


class AppTheme:
    @staticmethod
    def get_dark_theme() -> ft.Theme:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=AppColors.PRIMARY,
                secondary=AppColors.SECONDARY,
                surface=AppColors.DARK_BG,
                on_surface=AppColors.DARK_TEXT,
                on_surface_variant=AppColors.DARK_TEXT_DIM,
                error=AppColors.ERROR,
                on_primary=ft.Colors.WHITE,
                on_secondary=ft.Colors.WHITE,
                outline=AppColors.DARK_TEXT_MUTED,
                surface_tint=AppColors.TRANSPARENT,
            ),
            visual_density=ft.VisualDensity.COMFORTABLE,
        )

    @staticmethod
    def get_light_theme() -> ft.Theme:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=AppColors.PRIMARY,
                secondary=AppColors.SECONDARY,
                surface=AppColors.LIGHT_BG,
                on_surface=AppColors.LIGHT_TEXT,
                on_surface_variant=AppColors.LIGHT_TEXT_DIM,
                error=AppColors.ERROR,
                on_primary=ft.Colors.WHITE,
                on_secondary=ft.Colors.WHITE,
                outline=AppColors.LIGHT_TEXT_MUTED,
                surface_tint=AppColors.TRANSPARENT,
            ),
            visual_density=ft.VisualDensity.COMFORTABLE,
        )
