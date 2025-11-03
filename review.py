import os
from github import Github, Auth
import openai
import time
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
        auth = Auth.Token(github_token)
        g = Github(auth=auth)

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


def fetch_file_diffs(pr, max_chars=4000):
    files = pr.get_files()
    diffs = []
    for file in files:
        if any(file.filename.endswith(ext) for ext in [".lock", ".min.js", ".json"]):
            continue
        patch = file.patch or ""
        if patch:
            diffs.append((file.filename, patch[:max_chars]))
    return diffs


def request_code_review_for_file(filename, patch, client, retries=5):
    prompt = (
        f"Please review the following code diff for `{filename}`. "
        "Start with a score out of 10 for code quality, then list up to 3–4 clear, actionable suggestions. "
        "Reference specific lines or patterns where appropriate.\n\n"
        f"{patch}"
    )

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert senior software engineer performing a code review."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_completion_tokens=2048
            )
            return f"### Review for `{filename}`\n{response.choices[0].message.content.strip()}\n"
        except openai.error.RateLimitError:
            wait = 2 ** attempt
            print(f"Rate limit hit. Retrying in {wait}s...")
            time.sleep(wait)
        except Exception as e:
            return f"### Review for `{filename}`\nError: {e}\n"


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
        file_diffs = fetch_file_diffs(pr)

        all_reviews = ""
        for filename, patch in file_diffs:
            review = request_code_review_for_file(filename, patch, client)
            all_reviews += review + "\n---\n"

        post_review_comments(pr, all_reviews)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()