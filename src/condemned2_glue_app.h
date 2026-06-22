#pragma once

#include <memory>
#include <rex/rex_app.h>

#include "condemned2_glue_debug_overlay.h"

class Condemned2GlueApp : public rex::ReXApp {
public:
    using rex::ReXApp::ReXApp;

    static std::unique_ptr<rex::ui::WindowedApp> Create(
        rex::ui::WindowedAppContext& ctx);

    void OnCreateDialogs(rex::ui::ImGuiDrawer* drawer) override;

private:
    std::unique_ptr<c2::DebugOverlay> debugOverlay_;
};