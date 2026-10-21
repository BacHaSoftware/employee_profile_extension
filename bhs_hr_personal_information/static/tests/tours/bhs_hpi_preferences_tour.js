import { registry } from "@web/core/registry";

/**
 * An employee (internal user, not HR) fills his personal information in My Preferences
 * (data checked in tests/test_functional_ui.py).
 */
const field = (name) => `.modal .o_field_widget[name="${name}"] input`;

registry.category("web_tour.tours").add("bhs_hpi_preferences_tour", {
    steps: () => [
        {
            content: "Open the user menu",
            trigger: ".o_user_menu",
            run: "click",
            // First step after the page load: slower under coverage / right after -u
            timeout: 30000,
        },
        {
            content: "Open My Preferences",
            trigger: "[data-menu=preferences]",
            run: "click",
        },
        {
            content: "Open the Private tab",
            trigger: '.modal .o_notebook button.nav-link[name="private_information"]',
            run: "click",
            // the Preferences dialog waits for the default app (employee directory) to finish loading
            timeout: 30000,
        },
        {
            content: "Citizen ID",
            trigger: field("identification_id"),
            run: "edit 079090001234",
        },
        {
            content: "Issue date",
            trigger: field("cccd_issue_date"),
            run: "edit 03/15/2021",
        },
        {
            content: "Place of issue",
            trigger: field("cccd_issue_place"),
            run: "edit Police Ha Noi",
        },
        {
            content: "Birthday (core field)",
            trigger: field("birthday"),
            run: "edit 05/20/1990",
        },
        {
            content: "Save the preferences",
            trigger: '.modal button[name="preference_save"]',
            run: "click",
            // preference_save reloads the web client
            expectUnloadPage: true,
        },
        {
            content: "Web client reloaded, dialog closed",
            trigger: "body:not(.modal-open) .o_user_menu",
        },
    ],
});
