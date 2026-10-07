Feature: Quote enquiry form client-side validation and inline field errors (VNK-134)
  As a user
  I want the quote enquiry form to validate inputs on the client
  So that I can correct mistakes before submitting

  # Traceability:
  # Jira: VNK-134 (VNK-VNK-2-ENH-001)

  Background:
    Given I am on the Vinayaka File Works landing page

  @vnk-134 @happy
  Scenario: Valid submission sends request and shows Sending state
    When I fill the quote enquiry form with valid details
    And I submit the quote enquiry form
    Then the form shows a sending state
    And exactly one quote enquiry request is sent

  @vnk-134 @validation @negative
  Scenario Outline: Required field validation prevents submit and shows inline error
    When I fill the quote enquiry form with valid details except <field>
    And I submit the quote enquiry form
    Then no quote enquiry request is sent
    And an inline error is shown for <field>
    And focus moves to the first invalid field

    Examples:
      | field            |
      | name             |
      | mobile_number    |
      | product_category |

  @vnk-134 @validation @negative
  Scenario: Invalid email format shows inline error and prevents submit
    When I fill the quote enquiry form with valid details
    And I set the email to an invalid format
    And I submit the quote enquiry form
    Then no quote enquiry request is sent
    And an inline error is shown for email

  @vnk-134 @boundary @validation @negative
  Scenario Outline: Phone digits boundary validation prevents submit
    When I fill the quote enquiry form with valid details
    And I set the mobile number to <mobile>
    And I submit the quote enquiry form
    Then no quote enquiry request is sent
    And an inline error is shown for mobile_number

    Examples:
      | mobile              |
      | 123456789           |
      | 1234567890123456    |
      | 12345abcde          |

  @vnk-134 @regression
  Scenario: Inline error clears when user corrects the field
    When I submit the quote enquiry form with the name empty
    Then an inline error is shown for name
    When I type a valid name
    Then the inline error for name is cleared
