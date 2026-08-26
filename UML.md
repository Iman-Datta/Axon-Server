# UML Class Diagram – Axon

```mermaid
classDiagram

class User {
    - int id
    - String username
    - String email
    - String avatar
    - String github_username
}

class Organization {
    - int id
    - String name
    - String slug
    - String description
}

class OrganizationMember {
    - int id
    - String role
    - DateTime joined_at
}

class Workspace {
    - int id
    - String type
}

class Project {
    - int id
    - String name
    - String slug
    - String key
    - String visibility
    - bool is_archived
    - int ticket_sequence
}

class ProjectMember {
    - int id
    - String role
    - DateTime joined_at
}

class Epic {
    - int id
    - String name
    - String color
}

class Ticket {
    - int id
    - String ticket_number
    - String title
    - String type
    - String status
    - String kanban_column
    - String priority
    - int story_points
    - DateTime due_date
}

class GitHubIntegration {
    - int id
    - int repository_id
    - String repository_name
    - String default_branch
    - int webhook_id
    - bool is_active
}

class Activity {
    - int id
    - String verb
    - JSON metadata
    - DateTime created_at
}


User "1" --> "0..1" Workspace : owns
Organization "1" --> "0..1" Workspace : has

User "1" --> "0..*" OrganizationMember : joins
Organization "1" --> "0..*" OrganizationMember : contains

Workspace "1" --> "0..*" Project : contains
User "1" --> "0..*" Project : creates

User "1" --> "0..*" ProjectMember : joins
Project "1" --> "0..*" ProjectMember : contains

Project "1" --> "0..*" Epic : contains
User "1" --> "0..*" Epic : creates

Project "1" --> "0..*" Ticket : contains
Epic "0..1" --> "0..*" Ticket : groups
User "1" --> "0..*" Ticket : creates
User "0..1" --> "0..*" Ticket : assigned

Project "1" --> "0..1" GitHubIntegration : integrates
User "0..1" --> "0..*" GitHubIntegration : creates

Project "1" --> "0..*" Activity : records
Ticket "0..1" --> "0..*" Activity : relates
User "0..1" --> "0..*" Activity : performs