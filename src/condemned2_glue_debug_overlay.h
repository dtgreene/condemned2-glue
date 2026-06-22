#pragma once

#include <rex/ui/imgui_dialog.h>

namespace c2 {
	class DebugOverlay : public rex::ui::ImGuiDialog {
	public:
		explicit DebugOverlay(rex::ui::ImGuiDrawer* drawer);
		~DebugOverlay();

	protected:
		void OnDraw(ImGuiIO& io) override;
	};
}