(function () {
  const form = document.getElementById("assessment-form");
  if (!form) return;

  const sections = Array.from(form.querySelectorAll("[data-section]"));
  const bar = document.getElementById("assessment-progress");
  const label = document.getElementById("assessment-progress-label");
  const count = document.getElementById("assessment-progress-count");
  const error = document.getElementById("section-error");
  const prev = document.getElementById("prev-section");
  const next = document.getElementById("next-section");
  const submit = document.getElementById("submit-assessment");
  const steps = Array.from(document.querySelectorAll("#assessment-steps li"));
  let index = 0;

  function applicableQuestions(section) {
    return Array.from(section.querySelectorAll(".question")).filter(function (question) {
      return !question.classList.contains("d-none");
    });
  }

  function questionAnswered(question) {
    return Boolean(question.querySelector("input[type=radio]:checked"));
  }

  function sectionComplete(section) {
    return applicableQuestions(section).every(questionAnswered);
  }

  function refreshFollowUps(section) {
    const coreAnswers = Array.from(section.querySelectorAll('[data-core="true"] input[type=radio]:checked'));
    const showFollowUps = coreAnswers.some(function (input) {
      return Number(input.value) <= 2;
    });
    section.querySelectorAll('[data-follow-up="true"]').forEach(function (question) {
      question.classList.toggle("d-none", !showFollowUps);
      if (!showFollowUps) {
        question.querySelectorAll("input[type=radio]").forEach(function (input) {
          input.checked = false;
        });
      }
    });
  }

  function updateProgress() {
    let total = 0;
    let answered = 0;
    sections.forEach(function (section) {
      applicableQuestions(section).forEach(function (question) {
        total += 1;
        if (questionAnswered(question)) answered += 1;
      });
    });
    const percent = total ? Math.round((answered / total) * 100) : 0;
    bar.style.width = percent + "%";
    bar.setAttribute("aria-valuenow", String(percent));
    if (bar.parentElement) bar.parentElement.setAttribute("aria-valuenow", String(percent));
    label.textContent = "Section " + (index + 1) + " of " + sections.length;
    if (count) count.textContent = answered + " of " + total + " answered";
  }

  function show(nextIndex) {
    index = nextIndex;
    sections.forEach(function (section, sectionIndex) {
      section.classList.toggle("d-none", sectionIndex !== index);
    });
    prev.disabled = index === 0;
    next.classList.toggle("d-none", index === sections.length - 1);
    submit.classList.toggle("d-none", index !== sections.length - 1);
    steps.forEach(function (step, stepIndex) {
      const current = stepIndex === index;
      const done = stepIndex < index;
      step.classList.toggle("is-current", current);
      step.classList.toggle("is-done", done);
      const button = step.querySelector("button");
      if (button) button.disabled = !done && !current;
    });
    updateProgress();
  }

  steps.forEach(function (step, stepIndex) {
    const button = step.querySelector("button");
    if (!button) return;
    button.addEventListener("click", function () {
      if (!step.classList.contains("is-done")) return;
      error.classList.add("d-none");
      show(stepIndex);
    });
  });

  next.addEventListener("click", function () {
    if (!sectionComplete(sections[index])) {
      error.classList.remove("d-none");
      return;
    }
    error.classList.add("d-none");
    show(index + 1);
  });

  prev.addEventListener("click", function () {
    error.classList.add("d-none");
    show(index - 1);
  });

  form.addEventListener("change", function (event) {
    const section = event.target.closest("[data-section]");
    if (section) refreshFollowUps(section);
    updateProgress();
  });

  form.addEventListener("submit", function (event) {
    sections.forEach(refreshFollowUps);
    for (let sectionIndex = 0; sectionIndex < sections.length; sectionIndex += 1) {
      if (!sectionComplete(sections[sectionIndex])) {
        event.preventDefault();
        show(sectionIndex);
        error.classList.remove("d-none");
        return;
      }
    }
  });

  sections.forEach(refreshFollowUps);
  const invalid = form.querySelector(".is-invalid, .field-error");
  if (invalid) {
    const section = invalid.closest("[data-section]");
    const found = sections.indexOf(section);
    show(found >= 0 ? found : 0);
  } else {
    show(0);
  }
})();
