#include <imgui.h>

#include "condemned2_glue_debug_overlay.h"

namespace c2 {
	DebugOverlay::DebugOverlay(rex::ui::ImGuiDrawer* drawer) : rex::ui::ImGuiDialog(drawer) {
        //rex::ui::RegisterBind("bind_debug_space", "F8", "Pause menu", [this] {  });
    }
	DebugOverlay::~DebugOverlay() = default;

    void DebugOverlay::OnDraw(ImGuiIO& io) {
        const float W = io.DisplaySize.x, H = io.DisplaySize.y;
        if (W <= 0.0f || H <= 0.0f) return;

        ImGui::SetNextWindowPos(ImVec2(0, 0));
        ImGui::SetNextWindowSize(io.DisplaySize);
        ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
        ImGuiWindowFlags flags = ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoResize |
            ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoScrollbar |
            ImGuiWindowFlags_NoScrollWithMouse | ImGuiWindowFlags_NoBackground |
            ImGuiWindowFlags_NoInputs | ImGuiWindowFlags_NoNav |
            ImGuiWindowFlags_NoBringToFrontOnFocus |
            ImGuiWindowFlags_NoFocusOnAppearing | ImGuiWindowFlags_NoSavedSettings;

        if (!ImGui::Begin("##c2_debug_overlay", nullptr, flags)) {
            ImGui::End();
            ImGui::PopStyleVar();
            return;
        }

        ImDrawList* dl = ImGui::GetWindowDrawList();
        const ImVec2 p0(0, 0), p1(W, H);

        const ImVec2 text_pos(12.0f, 12.0f);
        const bool running = false;
        const ImU32 text_color =
            running
            ? IM_COL32(80, 255, 80, 255)
            : IM_COL32(255, 80, 80, 255);

        const char* status_text =
            running
            ? "render capture: on"
            : "render capture: off";

        // Optional dark backing box behind the text.
        const ImVec2 text_size = ImGui::CalcTextSize(status_text);
        dl->AddRectFilled(
            ImVec2(text_pos.x - 6.0f, text_pos.y - 4.0f),
            ImVec2(text_pos.x + text_size.x + 6.0f, text_pos.y + text_size.y + 4.0f),
            IM_COL32(0, 0, 0, 160),
            4.0f
        );

        // Draw the actual text.
        dl->AddText(text_pos, text_color, status_text);

        ImGui::End();
        ImGui::PopStyleVar();
    }
}