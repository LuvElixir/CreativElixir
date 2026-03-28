@tool
class_name CreativElixirEventBus
extends Node

# Chat flow signals
signal message_sent(text: String, context_mode: int, include_screenshot: bool)
signal response_received(result: Dictionary)
signal api_error(error_message: String)
signal request_started()
signal request_finished()

# Agent action signals
signal action_executed(action_name: String, success: bool, message: String)
signal actions_completed(results: Array)

# Context signals
signal context_gathered(context: Dictionary)
signal screenshot_ready(image: Image)

# UI signals
signal chat_cleared()
signal pop_out_requested()
signal dock_requested()
signal settings_requested()
signal art_panel_requested()

# Settings signals
signal settings_changed()
signal provider_changed(provider: String)
