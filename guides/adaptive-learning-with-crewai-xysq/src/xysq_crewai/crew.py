"""CrewAI crew definitions for the adaptive learning system.

Two crews with separate task configs to avoid agent resolution conflicts:
  • LearningCrew   — tutor teaches + quiz master generates questions
  • AssessmentCrew — quiz master evaluates + progress analyst reports
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class LearningCrew:
    """Teach a topic and generate an adaptive quiz."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/learning_tasks.yaml"

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def tutor(self) -> Agent:
        return Agent(config=self.agents_config["tutor"], verbose=False)  # type: ignore[index]

    @agent
    def quiz_master(self) -> Agent:
        return Agent(config=self.agents_config["quiz_master"], verbose=False)  # type: ignore[index]

    @task
    def teach_task(self) -> Task:
        return Task(config=self.tasks_config["teach_task"])  # type: ignore[index]

    @task
    def quiz_task(self) -> Task:
        return Task(config=self.tasks_config["quiz_task"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )


@CrewBase
class AssessmentCrew:
    """Evaluate quiz answers and generate a progress report."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/assessment_tasks.yaml"

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def quiz_master(self) -> Agent:
        return Agent(config=self.agents_config["quiz_master"], verbose=False)  # type: ignore[index]

    @agent
    def progress_analyst(self) -> Agent:
        return Agent(config=self.agents_config["progress_analyst"], verbose=False)  # type: ignore[index]

    @task
    def evaluate_task(self) -> Task:
        return Task(config=self.tasks_config["evaluate_task"])  # type: ignore[index]

    @task
    def report_task(self) -> Task:
        return Task(config=self.tasks_config["report_task"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )
