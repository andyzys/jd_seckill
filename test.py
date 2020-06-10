class Solution:
    def isValid(self, s: str) -> bool:
        if len(s) <= 1:
            return False

        stack = []
        s_map = {
            ")": "(",
            "]": "[",
            "}": "{"
        }
        stack.append(s[0])
        for i in range(1, len(s)):
            if stack[-1] == s_map.get(s[i], None):
                stack.pop(-1)
            else:
                stack.append(s[i])

        return True if len(stack) == 0 else False


solution = Solution()
print(solution.isValid("{[]}"))
