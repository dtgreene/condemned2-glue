#include <rex/ui/window.h>
#include <imgui.h>

#include "condemned2_glue_app.h"
#include "condemned2_glue_debug_overlay.h"
#include "generated\default\condemned2_glue_init.h"

std::unique_ptr<rex::ui::WindowedApp> Condemned2GlueApp::Create(
    rex::ui::WindowedAppContext& ctx) {
    return std::unique_ptr<Condemned2GlueApp>(
        new Condemned2GlueApp(ctx, "condemned2_glue", PPCImageConfig));
}

void Condemned2GlueApp::OnCreateDialogs(rex::ui::ImGuiDrawer* drawer) {
    if (window()) window()->SetTitle("Condemned 2: Bloodshot");

    debugOverlay_ = std::make_unique<c2::DebugOverlay>(drawer);
}
