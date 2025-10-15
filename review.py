import os
from github import Github
from openai import OpenAI

def initialize():
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not client:
            raise ValueError("Failed to initialize OpenAI client")

        # Get GitHub token
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN is not set")

        # Get repository info
        repo_name = os.getenv("GITHUB_REPOSITORY")
        if not repo_name:
            raise ValueError("GITHUB_REPOSITORY is not set")

        # Get PR number
        pr_id = os.getenv("PR_NUMBER")
        if not pr_id:
            raise ValueError("PR_NUMBER is not set")

        # Initialize GitHub instance
        g = Github(github_token)

        return client, g, repo_name, pr_id
    except Exception as e:
        raise ValueError(f"Initialization failed: {e}")


def get_repo_and_pull_request(g, repo_name, pr_id):
    try:
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(int(pr_id))
        return repo, pr
    except Exception as e:
        raise ValueError(f"Failed to fetch repo or PR: {e}")


def fetch_files_from_pr(pr, max_chars=4000):
    try:
        files = pr.get_files()
        diff = ""
        for file in files:
            if any(file.filename.endswith(ext) for ext in [".lock", ".min.js", ".json"]):
                continue

            patch = file.patch or ""
            diff += f"### File: {file.filename}\n{patch[:max_chars]}\n\n"

        if not diff:
            raise ValueError("No diff data found in PR (possibly all files ignored).")

        return diff
    except Exception as e:
        raise ValueError(f"Failed to fetch files from PR: {e}")


def request_code_review(diff, client):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # or "gpt-4o-mini" for cheaper reviews
            messages=[
                {"role": "system", "content": "You are an expert senior software engineer performing a code review."},
                {"role": "user", "content": (
                    "Please review the following code diff for potential issues, bugs, or improvements. "
                    "Start with a score out of 10 for code quality, then list up to 3–4 clear, actionable suggestions. "
                    "Reference specific lines or patterns where appropriate.\n\n"
                    f"{diff}"
                )}
            ],
            temperature=0.2,
            max_completion_tokens=2048
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise ValueError(f"Failed to get code review from OpenAI: {e}")


def post_review_comments(pr, review_comments):
    try:
        pr.create_issue_comment(f"AI Code Review Report\n\n{review_comments}")
        print("Code review posted successfully.")
    except Exception as e:
        raise ValueError(f"Failed to post review comments: {e}")


def main():
    try:
        client, g, repo_name, pr_id = initialize()
        repo, pr = get_repo_and_pull_request(g, repo_name, pr_id)
        diff = fetch_files_from_pr(pr)
        review_comments = request_code_review(diff, client)
        post_review_comments(pr, review_comments)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
